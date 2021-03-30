import json
import requests

from copy import deepcopy
from uuid import uuid4

import networkx as nx
import rdflib as rdf
import traitlets as trt


class SysML2LabeledPropertyGraph(trt.HasTraits):
    """A Labelled Property Graph for SysML v2.

    ..todo::
        Integrate it with the RDF representation.
    """

    FILTERED_DATA_KEYS = ("@context",)
    NEW_EDGES = {
        "owner": "OwnedBy",
    }

    graph: nx.MultiDiGraph = trt.Instance(nx.MultiDiGraph, args=tuple())

    merge: bool = trt.Bool(default=False)

    elements_by_id: dict = trt.Dict()

    nodes_by_type: dict = trt.Dict()
    edges_by_type: dict = trt.Dict()

    def __repr__(self):
        return (
            "<SysML v2 LPG: "
            f"{len(self.graph.nodes):,d} nodes, "
            f"{len(self.graph.edges):,d} edges"
            ">"
        )

    @property
    def nodes(self):
        return dict(self.graph.nodes)

    @property
    def edges(self):
        return dict(self.graph.edges)

    @property
    def node_types(self):
        return tuple(sorted({
            node_data.get("@type")
            for node_id, node_data in self.graph.nodes.data()
            if node_data.get("@type", False)
        }))

    @property
    def edge_types(self):
        return tuple(sorted({
            edge_type
            for *_, edge_type in self.graph.edges
        }))

    def __getitem__(self, *args):
        return self.graph.__getitem__(*args)

    @trt.observe("elements_by_id")
    def _update_elements(self, *_):
        self.update(elements=self.elements_by_id)

    def update(self, elements: dict, merge=None):
        if merge is None:
            merge = self.merge
        new_edges = [
            [
                element_id,                                 # source
                data[key]["@id"],                           # target
                edge_type,                                  # edge type
                {                                           # edge data
                    "@id": f"_{uuid4()}",
                    "source": [{"@id": element_id}],
                    "target": [{"@id": data[key]["@id"]}],
                    "@type": f"_{edge_type}",
                    "relatedElement": [
                        {"@id": element_id},
                        {"@id": data[key]["@id"]},
                    ],
                },
            ]
            for element_id, data in elements.items()
            for key, edge_type in self.NEW_EDGES.items()
            if (data.get(key, {}) or {}).get("@id")
        ]

        filtered_keys = list(self.FILTERED_DATA_KEYS) + list(self.NEW_EDGES)
        elements = {
            key: value
            for key, value in elements.items()
            if key not in filtered_keys
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

        with self.hold_trait_notifications():
            if not merge:
                old_graph = self.graph
                self.graph = nx.MultiDiGraph()
                del old_graph

            self.graph.add_nodes_from(
                {
                    id_: elements[id_]
                    for id_ in non_relationship_element_ids
                }.items()
            )
            self.graph.add_edges_from([
                [
                    relation["relatedElement"][0]["@id"],  # source node (str id)
                    relation["relatedElement"][1]["@id"],  # target node (str id)
                    relation["@type"],                     # edge type (str name)
                    relation,                              # edge data (dict)
                ]
                for relation in relationships
            ] + new_edges)

    def filter(
            self,
            *,
            nodes: (list, set, tuple) = None,
            node_types: (list, tuple, str) = None,
            edges: (list, set, tuple) = None,
            edge_types: (list, tuple, str) = None,
    ):
        graph = self.graph
        subgraph = graph.__class__()

        nodes = nodes or self.graph.nodes
        edges = edges or self.graph.edges

        node_types = node_types or self.node_types
        if isinstance(node_types, str):
            node_types = [node_types]
        edge_types = edge_types or []
        if isinstance(edge_types, str):
            edge_types = [edge_types]

        if edge_types:
            edges += [
                (source, target, data)
                for (source, target, type_), data in edges.items()
                if type_ in edge_types
            ]

        if not edges:
            print(f"Could not find any edges of type: '{edge_types}'!")
            return subgraph

        nodes = {
            node_id: graph.nodes[node_id]
            for node_id in sum([  # sum(a_list, []) flattens a_list
            [source, target]
            for (source, target, data) in edges
        ], [])
            if node_id in nodes
            and self.elements_by_id[node_id]["@type"] in node_types
        }

        subgraph.add_nodes_from(nodes.items())
        subgraph.add_edges_from(edges)

        return subgraph


class SysML2RDFGraph(trt.HasTraits):
    """A Resource Description Framework (RDF) Graph for SysML v2 data."""

    _cached_contexts: dict = trt.Instance(dict, args=tuple())
    graph: rdf.Graph = trt.Instance(rdf.Graph, args=tuple())

    def import_context(self, jsonld_item: dict) -> dict:
        jsonld_item = deepcopy(jsonld_item)
        context_url = jsonld_item.get("@context", {}).get("@import", None)
        if not context_url:
            return jsonld_item
        if context_url not in self._cached_contexts:
            response = requests.get(context_url)
            if not response.ok:
                raise requests.HTTPError(response.reason)
            data = response.json()
            if "@context" not in data:
                raise ValueError(
                    f"Download context does not have a @context key: {list(data.keys())}"
                )
            self._cached_contexts[context_url] = data["@context"]
        jsonld_item["@context"].update(self._cached_contexts[context_url])
        return jsonld_item
    
    def __repr__(self):
        return (
            "<SysML v2 RDF Graph: "
            f"{len(self.graph):,d} triples, "
            f"{len(set(self.graph.predicates())):,d} unique predicates"
            ">"
        )

    def update(self, elements: dict, merge=False):
        if not merge:
            old_graph = self.graph
            self.graph = rdf.Graph()
            del old_graph

        elements = [
            self.import_context(element)
            for element in elements.values()
        ]
        self.graph.parse(
            data=json.dumps(elements),
            format="application/ld+json",
        )
