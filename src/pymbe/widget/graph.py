import ipywidgets as ipyw
import traitlets as trt

from ..graph import SysML2LabeledPropertyGraph
from .diagram import SysML2ElkDiagram


class SysML2LPGWidget(SysML2LabeledPropertyGraph, ipyw.HBox):
    """An ipywidget to interact with a SysML2 model through an LPG."""

    diagram: SysML2ElkDiagram = trt.Instance(SysML2ElkDiagram, args=())
    edge_type_selector = trt.Instance(ipyw.SelectMultiple, args=())
    node_type_selector = trt.Instance(ipyw.SelectMultiple, args=())

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        return [
            ipyw.VBox(
                [
                    ipyw.HTML("<h2>Node Types</h2>"),
                    self.node_type_selector,
                    ipyw.HTML("<h2>Edge Types</h2>"),
                    self.edge_type_selector,
                ],
                layout=ipyw.Layout(width="25%"),
            ),
            self.diagram,
        ]

    @trt.validate("layout")
    def _validate_layout(self, proposal):
        layout = proposal.value
        # TODO: if necessary, manipulate the layout here
        return layout

    @trt.observe("graph")
    def _updated_type_selector_options(self, *_):
        nodes_by_type = {
            node_type: [
                node
                for node in self.nodes
                if self.nodes[node].get("@type", None) == node_type
            ]
            for node_type in self.node_types
        }
        self.node_type_selector.options = {
            f"{node_type} [{len(nodes)}]": nodes
            for node_type, nodes in sorted(nodes_by_type.items())
        }

        edges_by_type = {
            an_edge_type: [
                (source, target, edge_type)
                for source, target, edge_type in self.edges
                if edge_type == an_edge_type
            ]
            for an_edge_type in self.edge_types
        }
        self.edge_type_selector.options = {
            f"{edge_type} [{len(edges)}]": edges
            for edge_type, edges in sorted(edges_by_type.items())
            if edge_type in self.edge_types
        }

    @property
    def selected_nodes_by_type(self):
        node_ids = set(sum(map(list, self.node_type_selector.value), []))
        return tuple(
            self.graph.nodes[id_]
            for id_ in sorted(node_ids)
            if id_ in self.graph.nodes
        )

    @property
    def selected_edges_by_type(self):
        edge_ids = set(sum(map(list, self.edge_type_selector.value), []))
        return tuple(
            self.graph.edges[id_]
            for id_ in sorted(edge_ids)
            if id_ in self.graph.edges
        )
