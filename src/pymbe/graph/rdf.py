import json
import requests

from copy import deepcopy

import rdflib as rdf
import traitlets as trt

from ..core import Base


class SysML2RDFGraph(Base):
    """A Resource Description Framework (RDF) Graph for SysML v2 data."""

    _cached_contexts: dict = trt.Instance(dict, args=tuple())
    graph: rdf.Graph = trt.Instance(rdf.Graph, args=tuple())
    merge: bool = trt.Bool(default_value=False)

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
                    "Download context does not have a "
                    f"@context key: {list(data.keys())}"
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

    def update(self, elements: dict):
        if not self.merge:
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
