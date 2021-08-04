import json
from copy import deepcopy
from warnings import warn

import rdflib as rdf
import requests
import traitlets as trt

from ..model import Model


class SysML2RDFGraph(trt.HasTraits):
    """A Resource Description Framework (RDF) Graph for SysML v2 data."""

    model: Model = trt.Instance(Model, allow_none=True)
    graph: rdf.Graph = trt.Instance(rdf.Graph, args=())
    merge: bool = trt.Bool(default_value=False)

    _cached_contexts: dict = trt.Instance(dict, args=())

    # TODO: bring in the context through the static @type routes

    def import_context(self, jsonld_item: dict) -> dict:
        jsonld_item = deepcopy(jsonld_item)
        # FIXME: Migrate to the new form of the Pilot Implementation
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

    @trt.observe("model")
    def update(self, *_):
        if not self.merge:
            old_graph = self.graph
            self.graph = rdf.Graph()
            warn(f"Deleting old graph: {old_graph}")
            del old_graph

        elements = [self.import_context(element) for element in self.model.elements.values()]
        self.graph.parse(
            data=json.dumps(elements),
            format="application/ld+json",
        )
