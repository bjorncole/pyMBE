import ipywidgets as ipyw
import traitlets as trt

from ..graph import SysML2LabeledPropertyGraph
from .core import BaseWidget
from .diagram import SysML2ElkDiagram


class SysML2LPGWidget(SysML2LabeledPropertyGraph, BaseWidget, ipyw.Box):
    """An ipywidget to interact with a SysML2 model through an LPG."""

    description = trt.Unicode("Diagram").tag(sync=True)
    diagram: SysML2ElkDiagram = trt.Instance(
        SysML2ElkDiagram,
        kw=dict(layout=dict(width="100%", height="100vh")),
    )
    edge_type_selector: ipyw.SelectMultiple = trt.Instance(
        ipyw.SelectMultiple,
        args=(),
    )
    node_type_selector: ipyw.SelectMultiple = trt.Instance(
        ipyw.SelectMultiple,
        args=(),
    )
    update_diagram: ipyw.Button = trt.Instance(ipyw.Button)
    selector_link: trt.link = trt.Instance(trt.link, allow_none=True)

    @trt.default("update_diagram")
    def _make_update_diagram_button(self) -> ipyw.Button:
        button = ipyw.Button(
            description="",
            icon="retweet",
            tooltip="Update diagram",
            layout=dict(height="40px", width="40px")
        )
        button.on_click(self._update_diagram_graph)
        return button

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        self._update_diagram_toolbar()
        self._update_diagram_observers()
        return [self.diagram]

    @trt.validate("layout")
    def _validate_layout(self, proposal):
        layout = proposal.value
        layout.height = "100%"
        layout.width = "auto"
        return layout

    @trt.observe("diagram")
    def _update_diagram_observers(self, *_):
        if self.selector_link:
            self.selector_link.unlink()
        self.selector_link = trt.link(
            (self, "selected"),
            (self.diagram.elk_app.diagram, "selected"),
        )

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

        self.diagram.graph = self.graph

    @trt.observe("edge_type_selector", "node_type_selector")
    def _update_observers_for_selectors(self, change: trt.Bunch):
        if not change:
            return
        if change.old:
            change.old.unobserve(self._update_filtered_graph)
        if change.new:
            change.new.observe(self._update_filtered_graph, "value")

    def _update_diagram_graph(self, *_):
        self.diagram.graph = self.filter(
            nodes=self.selected_by_type_node_ids,
            edges=self.selected_by_type_edge_ids,
        )
        # TODO: look into adding a refresh, e.g.,
        # self.diagram.elk_app.refresh()

    @property
    def selected_by_type_node_ids(self):
        return tuple(set(sum(map(list, self.node_type_selector.value), [])))

    @property
    def selected_by_type_nodes(self):
        return tuple(
            self.graph.nodes[id_]
            for id_ in sorted(self.selected_by_type_node_ids)
            if id_ in self.graph.nodes
        )

    @property
    def selected_by_type_edge_ids(self):
        return tuple(set(sum(map(list, self.edge_type_selector.value), [])))

    @property
    def selected_by_type_edges(self):
        return tuple(
            self.graph.edges[id_]
            for id_ in sorted(self.selected_by_type_edge_ids)
            if id_ in self.graph.edges
        )

    def _update_diagram_toolbar(self):
        # Append elements to the elk_app toolbar
        diagram = self.diagram
        accordion = {**diagram.toolbar_accordion}
        accordion.update({
            "Edge Types": self.edge_type_selector,
            "Node Types": self.node_type_selector,
        })

        buttons = [*diagram.toolbar_buttons]
        buttons += [self.update_diagram]

        with diagram.hold_trait_notifications():
            diagram.toolbar_accordion = accordion
            diagram.toolbar_buttons = buttons
