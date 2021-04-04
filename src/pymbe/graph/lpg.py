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

    @property
    def nodes(self):
        return dict(self.graph.nodes)

    @property
    def edges(self):
        return dict(self.graph.edges)

    @property
    def node_types(self):
        return tuple(sorted(self.nodes_by_type))

    @property
    def edge_types(self):
        return tuple(sorted(self.edges_by_type))

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

    def get_path(self,
            selected: (list, set, tuple),
            directional: bool = True,
            excluded_edge_types: (list, set, tuple) = None,
            reversed_edge_types: (list, set, tuple) = None,
        ):
        """Make a subgraph with the shortest paths between two selected nodes"""
        excluded_edge_types = excluded_edge_types or []
        reversed_edge_types = reversed_edge_types or []

        if len(selected) != 2 or not all(isinstance(n, str) for n in selected):
            print("Can only work with two elements selected")
            return None

        if reversed_edge_types and not directional:
            raise ValueError(
                f"Reversing edge types: {reversed_edge_types} makes no "
                "sense since directional is False")

        edges = [
            (edge[::-1][1:])
            if edge[2] in reversed_edge_types
            else [*edge[:2]] + [edge[2]]
            for edge in self.graph.edges
        ]
        if excluded_edge_types:
            edges = [
                (source, target, type_)
                for source, target, type_ in edges
                if type_ not in excluded_edge_types
            ]

        if directional:
            path_graph = nx.MultiDiGraph()
        else:
            path_graph = nx.MultiGraph()
        path_graph.add_edges_from(edges)

        source, target = selected
        try:
            nodes = set(sum(
                map(list, nx.all_shortest_paths(path_graph, source, target)),
                []))
            subgraph = nx.MultiDiGraph(self.graph.subgraph(nodes))
            if excluded_edge_types:
                subgraph.remove_edges_from([
                    edge
                    for edge in subgraph.edges
                    if edge[2] in excluded_edge_types
                ])
            return subgraph
        except (nx.NetworkXError, nx.NetworkXException) as exc:
            self.log.warning(exc)
            return None
