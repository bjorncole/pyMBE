import json
import requests

from copy import deepcopy

import networkx as nx
import rdflib as rdf
import traitlets as trt


class SysML2LabeledPropertyGraph(trt.HasTraits):
    """A Labelled Property Graph for SysML v2.
    
    ..todo::
        Integrate it with the RDF representation.
    """

    graph = trt.Instance(nx.MultiDiGraph, args=tuple())

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
    
    def __getitem__(self, *args):
        return self.graph.__getitem__(*args)

    def update(self, client, merge=False):
        if not merge:
            old_graph = self.graph
            self.graph = nx.MultiDiGraph()
            del old_graph
            
        elements_by_id = client.elements_by_id

        relationship_element_ids = {
            element_id
            for element_id, element in elements_by_id.items()
            if "relatedElement" in element
        }
        non_relationship_element_ids = set(
            elements_by_id
        ).difference(relationship_element_ids)
        
        self.graph.add_nodes_from(
            {
                id_: elements_by_id[id_]
                for id_ in non_relationship_element_ids
            }.items()
        )
        relationships = [
            elements_by_id[id_]
            for id_ in relationship_element_ids
        ]
        self.graph.add_edges_from([
            [
                relation["relatedElement"][0]["@id"],  # source node (str id)
                relation["relatedElement"][1]["@id"],  # target node (str id)
                relation["@type"],                     # edge type (str name)
                relation,                              # edge data (dict)
            ]
            for relation in relationships
        ])
    
    @staticmethod
    def set_layout_option(widget, category: str, option: str, value):
        """Set a layout option"""
        category_idxs = [
            int(idx)
            for idx, name in widget._titles.items()
            if name == category
        ]
        if len(category_idxs) != 1:
            raise ValueError(f"Found {len(category_idxs)} entries for '{category}'!")
        category_widget = widget.children[category_idxs[0]]

        option_idxs = [
            int(idx)
            for idx, name in category_widget._titles.items()
            if name == option
        ]
        if len(option_idxs) != 1:
            raise ValueError(f"Found {len(option_idxs)} entries for '{option}' under '{category}'!")

        category_widget.children[option_idxs[0]].value = value


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

    def update(self, client, merge=False):
        if not merge:
            old_graph = self.graph
            self.graph = rdf.Graph()
            del old_graph

        elements = [
            self.import_context(element)
            for element in client.elements_by_id.values()
        ]
        self.graph.parse(
            data=json.dumps(elements),
            format="application/ld+json",
        )
