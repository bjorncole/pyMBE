from uuid import uuid4

import networkx as nx
import traitlets as trt

from ..core import Base


class SysML2LabeledPropertyGraph(Base):
    """A Labelled Property Graph for SysML v2.

    ..todo::
        Integrate it with the RDF representation.
    """

    FILTERED_DATA_KEYS: tuple = ("@context",)
    ATTRIBUTE_TO_EDGES: tuple = (
        # dict(attribute="owner", new_type="Owned", reversed=True),
    )

    graph: nx.MultiDiGraph = trt.Instance(nx.MultiDiGraph, args=tuple())

    merge: bool = trt.Bool(default=False)

    nodes: dict = trt.Dict()
    edges: dict = trt.Dict()

    node_types: tuple = trt.Tuple()
    edge_types: tuple = trt.Tuple()

    nodes_by_type: dict = trt.Dict()
    edges_by_type: dict = trt.Dict()

    def __repr__(self):
        return (
            "<SysML v2 LPG: "
            f"{len(self.graph.nodes):,d} nodes, "
            f"{len(self.graph.edges):,d} edges"
            ">"
        )

    def __getitem__(self, *args):
        return self.graph.__getitem__(*args)

    @staticmethod
    def _make_new_edge(data: dict, edge_mapper: dict) -> list:
        attribute = edge_mapper["attribute"]
        if not data.get(attribute, {}):
            return []
        edge_type = edge_mapper["new_type"]
        sources = [data["@id"]]
        targets =data[attribute]
        if isinstance(targets, (list, tuple, set)):
            targets = [
                t["@id"] for t in targets
            ]
            sources *= len(targets)
        elif isinstance(targets, dict):
            targets = [targets["@id"]]
        else:
            raise ValueError(
                f"Cannot process: {targets} of type: {type(targets)}."
            )
        if edge_mapper.get("reversed", False):
            sources, targets = targets, sources
        return [
            [
                source,                           # source
                target,                           # target
                edge_type,                        # edge type
                {                                 # edge data
                    "@id": f"_{uuid4()}",
                    "source": [{"@id": source}],
                    "target": [{"@id": target}],
                    "@type": f"_{edge_type}",
                    "relatedElement": [
                        {"@id": source},
                        {"@id": target},
                    ],
                },
            ] for source, target in zip(sources, targets)
        ]

    def update(self, elements: dict, merge=None):
        merge = self.merge if merge is None else merge

        new_edges = [
            self._make_new_edge(data=element_data, edge_mapper=edge_mapper)
            for element_id, element_data in elements.items()
            for edge_mapper in self.ATTRIBUTE_TO_EDGES
        ]
        # flatten new edges
        new_edges = sum(new_edges, [])

        filtered_keys = list(self.FILTERED_DATA_KEYS) + [
            edge_mapper["attribute"]
            for edge_mapper in self.ATTRIBUTE_TO_EDGES
        ]
        elements = {
            element_id: {
                key: value
                for key, value in element_data.items()
                if key not in filtered_keys
            }
            for element_id, element_data in elements.items()
        }

        relationship_element_ids = {
            element_id
            for element_id, element in elements.items()
            if "relatedElement" in element
        }
        non_relationship_element_ids = set(elements).difference(
            relationship_element_ids
        )

        relationships = [
            elements[element_id]
            for element_id in relationship_element_ids
        ]

        graph = nx.MultiDiGraph()
        if merge:
            graph.add_nodes_from(self.graph)
            graph.add_edges_from(self.graph)

        old_graph = self.graph
        del old_graph

        graph.add_nodes_from(
            {
                id_: elements[id_]
                for id_ in non_relationship_element_ids
            }.items()
        )
        graph.add_edges_from([
            [
                relation["relatedElement"][0]["@id"],  # source node (str id)
                relation["relatedElement"][1]["@id"],  # target node (str id)
                relation["@type"],                     # edge type (str name)
                relation,                              # edge data (dict)
            ]
            for relation in relationships
        ] + new_edges)

        with self.hold_trait_notifications():
            self.nodes = dict(graph.nodes)
            self.edges = dict(graph.edges)

            self.node_types = tuple(sorted({
                node["@type"]
                for node in self.nodes.values()
                if "@type" in node
            }))
            self.edge_types = tuple(sorted({
                edge["@type"]
                for edge in self.edges.values()
                if "@type" in edge
            }))

            self.nodes_by_type = {
                node_type: [
                    node
                    for node in graph.nodes
                    if graph.nodes[node].get("@type", None) == node_type
                ]
                for node_type in self.node_types
            }

            self.edges_by_type = {
                edge_type: [
                    edge
                    for edge in graph.edges
                    if edge[2] == edge_type
                ]
                for edge_type in self.edge_types
            }

            self.graph = graph

    def filter(
            self,
            *,
            nodes: (list, set, tuple) = None,
            node_types: (list, tuple, str) = None,
            edges: (list, set, tuple) = None,
            edge_types: (list, tuple, str) = None,
            reverse_edge_types: (list, tuple, str) = None,
    ):
        graph = self.graph
        subgraph = graph.__class__()

        nodes = nodes or ([] if node_types else list(self.graph.nodes))
        edges = edges or ([] if edge_types else list(self.graph.edges))

        node_types = node_types or ([] if nodes else self.node_types)
        if isinstance(node_types, str):
            node_types = [node_types]

        edge_types = edge_types or ([] if edges else self.edge_types)
        if isinstance(edge_types, str):
            edge_types = [edge_types]

        reverse_edge_types = reverse_edge_types or []
        if isinstance(reverse_edge_types, str):
            reverse_edge_types = [reverse_edge_types]

        edges = list(set(edges))
        if edge_types:
            edges += [
                (source, target, type_)
                for (source, target, type_) in self.graph.edges
                if type_ in edge_types
            ]

        if not edges:
            print(f"Could not find any edges of type: '{edge_types}'!")
            return subgraph

        nodes = {
            node_id
            for node_id in set(sum([  # sum(a_list, []) flattens a_list
                [source, target]
                for (source, target, type_) in edges
            ], []))
            if node_id in nodes
            or self.graph.nodes[node_id].get("@type", None) in node_types
        }
        edges = set(edges)
        subgraph.add_nodes_from((
            [node, self.graph.nodes[node]]
            for node in nodes
        ))
        subgraph.add_edges_from(
            [
                *(
                    (target, source, type_) if type_ in reverse_edge_types
                    else (source, target, type_)
                ),
                self.graph.edges[(source, target, type_)]
            ]
            for source, target, type_ in edges
        )

        return subgraph

    def _get_subgraph(self,
        directional: bool = True,
        excluded_edge_types: (list, set, tuple) = None,
        excluded_node_types: (list, set, tuple) = None,
        reversed_edge_types: (list, set, tuple) = None,
    ):
        excluded_edge_types = excluded_edge_types or []
        excluded_node_types = excluded_node_types or []
        reversed_edge_types = reversed_edge_types or []

        if reversed_edge_types and not directional:
            raise ValueError(
                f"Reversing edge types: {reversed_edge_types} makes no "
                "sense since directional is False")

        included_nodes = sum(
            [
                nodes
                for node_type, nodes in self.nodes_by_type.items()
                if node_type not in excluded_node_types
            ],
            [],
        )
        graph = self.graph.__class__(self.graph.subgraph(included_nodes))

        edges = [
            (edge[::-1][1:])
            if edge[2] in reversed_edge_types
            else [*edge[:2]] + [edge[2]]
            for edge in graph.edges
        ]
        if excluded_edge_types:
            edges = [
                (source, target, type_)
                for source, target, type_ in edges
                if type_ not in excluded_edge_types
            ]

        if directional:
            subgraph = nx.MultiDiGraph()
        else:
            subgraph = nx.MultiGraph()
        subgraph.add_edges_from(edges)
        return subgraph

    def _filter_subgraph(
        self,
        subgraph: nx.Graph,
        excluded_edge_types: (list, set, tuple) = None,
        excluded_node_types: (list, set, tuple) = None,
    ):
        return subgraph

    def get_path(self,
            source: str,
            target: str,
            directional: bool = True,
            excluded_edge_types: (list, set, tuple) = None,
            excluded_node_types: (list, set, tuple) = None,
            reversed_edge_types: (list, set, tuple) = None,
        ):
        """Make a subgraph with the shortest paths between two selected nodes"""

        path_graph = self._get_subgraph(
            directional=directional,
            excluded_edge_types=excluded_edge_types,
            excluded_node_types=excluded_node_types,
            reversed_edge_types=reversed_edge_types,
        )

        try:
            nodes = set(sum(
                map(list, nx.all_shortest_paths(path_graph, source, target)),
                []))
            subgraph = nx.MultiDiGraph(self.graph.subgraph(nodes))
            return subgraph
        except (nx.NetworkXError, nx.NetworkXException) as exc:
            self.log.warning(exc)
            return None

    def get_spanning_subgraph_from_seeds(
        self,
        seeds: (list, set, tuple),
        max_distance: int = 2,
        directional: bool = True,
        excluded_edge_types: (list, set, tuple) = None,
        excluded_node_types: (list, set, tuple) = None,
        reversed_edge_types: (list, set, tuple) = None,
    ):
        graph = self._get_subgraph(
            directional=directional,
            excluded_edge_types=excluded_edge_types,
            excluded_node_types=excluded_node_types,
            reversed_edge_types=reversed_edge_types,
        )

        seed_nodes = {
            id_: max_distance
            for id_ in seeds
            if id_ in graph.nodes
        }
        seed_elements = [
            self.elements_by_id[id_]
            for id_ in seeds
            if id_ not in seed_nodes
            and id_ in self.elements_by_id
        ]
        seed_edges = [
            [element["relatedElement"][0]["@id"],
             element["relatedElement"][1]["@id"]]
            for element in seed_elements
            if len(element.get("relatedElement")) == 2
        ]

        distances = {
            node: max_distance - 1
            for node in set(sum(seed_edges, []))
            if node in graph
        }
        distances.update(seed_nodes)

        max_iter = 100
        while sum(distances.values()) > 0 and max_iter > 0:
            max_iter -= 1
            for node_id, distance in tuple(distances.items()):
                if distance < 1:
                    continue
                for neighbor in graph.neighbors(node_id):
                    distances[neighbor] = distances.get(neighbor, distance - 1)
                distances[node_id] -= 1

        nodes = tuple(distances)

        return nx.MultiDiGraph(self.graph.subgraph(nodes))
