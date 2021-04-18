from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from uuid import uuid4
from warnings import warn

import networkx as nx
import ruamel.yaml as yaml
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
    SYSML_SUBGRAPH_RECIPES: dict = yaml.load(
        (Path(__file__).parent / "sysml_subgraphs.yml").read_text(),
        Loader=yaml.RoundTripLoader,
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
        self._adapt.cache_clear()

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

    def get_projection(self, projection: str) -> nx.Graph:
        instructions = self.SYSML_SUBGRAPH_RECIPES.get(projection)
        if not instructions:
            raise ValueError(
                f"Could not find SysML Project: '{projection}'.\n"
                f"Options available are: {tuple(SYSML_SUBGRAPH_RECIPES)}"
            )

        for key in tuple(instructions):
            if key.startswith("included_") and key.endswith("_types"):
                # revert included for excluded types
                included_types = instructions.pop(key)
                types_key = key.replace("included_", "")
                types = set(getattr(self, types_key)).difference(included_types)
                instructions[f"excluded_{types_key}"] = tuple(sorted(types))

        function_attributes = self.adapt.__annotations__
        instructions = {
            key: value
            for key, value in instructions.items()
            if key in function_attributes
        }

        return self.adapt(**instructions)


    def adapt(self,
        excluded_node_types: (list, set, tuple) = None,
        excluded_edge_types: (list, set, tuple) = None,
        reversed_edge_types: (list, set, tuple) = None,
    ) -> nx.Graph:
        """
            Using the existing graph, filter by node and edge types, and/or
            reverse certain edge types.
        """
        excluded_edge_types = excluded_edge_types or []
        excluded_node_types = excluded_node_types or []
        reversed_edge_types = reversed_edge_types or []

        return self._adapt(
            excluded_edge_types=tuple(sorted(excluded_edge_types)),
            excluded_node_types=tuple(sorted(excluded_node_types)),
            reversed_edge_types=tuple(sorted(reversed_edge_types)),
        ).copy()

    @lru_cache
    def _adapt(self,
        excluded_node_types: (list, set, tuple) = None,
        excluded_edge_types: (list, set, tuple) = None,
        reversed_edge_types: (list, set, tuple) = None,
    ):

        graph = self.graph

        mismatched_node_types = set(excluded_node_types).difference(self.node_types)
        if mismatched_node_types:
            warn(f"These node types are not in the graph: {mismatched_node_types}.")

        mismatched_edge_types = {
            (*excluded_edge_types, *reversed_edge_types)
        }.difference(self.edge_types)
        if mismatched_edge_types:
            warn(f"These edge types are not in the graph: {mismatched_edge_types}.")

        included_nodes = sum(
            [
                nodes
                for node_type, nodes in self.nodes_by_type.items()
                if node_type not in excluded_node_types
            ],
            [],
        )
        subgraph = graph.__class__(graph.subgraph(included_nodes))

        def _process_edge(src, tgt, typ, data, rev_types):
            if typ in rev_types:
                tgt, src = src, tgt
                typ += "^-1"
                data = deepcopy(data)
                data["@type"] = typ
            return src, tgt, typ, data

        edges = [
            _process_edge(src, tgt, typ, data, reversed_edge_types)
            for (src, tgt, typ), data in subgraph.edges.items()
            if typ not in excluded_edge_types
        ]

        new_graph = graph.__class__()
        new_graph.add_edges_from(edges)
        return new_graph

    @staticmethod
    def _make_undirected(graph):
        if graph.is_multigraph():
            return nx.MultiGraph(graph)
        else:
            return nx.Graph(graph)

    def get_path_graph(
        self,
        graph: nx.Graph,
        source: str,
        target: str,
        directed: bool = True,
    ):
        """Make a new graph with the shortest paths between two nodes"""
        if not directed:
            graph = self._make_undirected(graph)
        try:
            nodes = set(sum(map(
                list,
                nx.all_shortest_paths(graph, source, target)
            ), []))
            return graph.__class__(graph.subgraph(nodes))

        except (nx.NetworkXError, nx.NetworkXException) as exc:
            self.log.warning(exc)
            return None

    def get_spanning_graph(
        self,
        graph: nx.Graph,
        seeds: (list, set, tuple),
        max_distance: int = 2,
        directed: bool = True,
    ):
        if not directed:
            graph = self._make_undirected(graph)
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

        return graph.__class__(graph.subgraph(nodes))
