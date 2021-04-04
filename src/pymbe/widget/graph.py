import ipywidgets as ipyw
import traitlets as trt

from ..graph import SysML2LabeledPropertyGraph
from .core import BaseWidget
from .diagram import SysML2ElkDiagram


@ipyw.register
class SysML2LPGWidget(SysML2LabeledPropertyGraph, BaseWidget, ipyw.Box):
    """An ipywidget to interact with a SysML2 model through an LPG."""

    description = trt.Unicode("Diagram").tag(sync=True)
    diagram: SysML2ElkDiagram = trt.Instance(
        SysML2ElkDiagram,
        kw=dict(layout=dict(width="100%", height="100vh")),
    )
    edge_type_selector: ipyw.SelectMultiple = trt.Instance(
        ipyw.SelectMultiple,
        kw=dict(rows=10),
    )
    edge_type_reverser: ipyw.SelectMultiple = trt.Instance(
        ipyw.SelectMultiple,
        kw=dict(rows=10),
    )
    node_type_selector: ipyw.SelectMultiple = trt.Instance(
        ipyw.SelectMultiple,
        kw=dict(rows=10),
    )
    update_diagram: ipyw.Button = trt.Instance(ipyw.Button)
    filter_to_path: ipyw.Button = trt.Instance(ipyw.Button)
    path_directionality: ipyw.Checkbox = trt.Instance(
        ipyw.Checkbox,
        kw=dict(
            default_value=False,
            description="Enforce Edge Directions",
        ),
    )

    filter_by_dist: ipyw.Button = trt.Instance(ipyw.Button)
    max_distance: ipyw.IntSlider = trt.Instance(
        ipyw.IntSlider,
        kw=dict(default_valud=1, min=1, max=4),
    )

    # Revisit this when the diagram selector mapper is fixed
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

    @trt.default("filter_to_path")
    def _make_filter_to_path_button(self) -> ipyw.Button:
        button = ipyw.Button(
            description="",
            icon="project-diagram",  # share-alt
            tooltip="Filter To Path",
            layout=dict(height="40px", width="40px")
        )
        button.on_click(self._update_diagram_graph)
        return button

    @trt.default("filter_by_dist")
    def _make_filter_by_dist_button(self) -> ipyw.Button:
        button = ipyw.Button(
            description="",
            icon="sitemap",  # hubspot
            tooltip="Filter by Distance",
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
        # TODO: add back in after resolving issue with ipyelk indexing
        pass
        # if self.selector_link:
        #     self.selector_link.unlink()
        # self.selector_link = trt.link(
        #     (self, "selected"),
        #     (self.diagram.elk_app.diagram, "selected"),
        # )

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

        self.edge_type_reverser.options = self.edge_types
        self.diagram.graph = self.graph

    def _update_diagram_graph(self, button=None):
        if button is self.filter_to_path:
            included_edges = self.edge_type_selector.value
            if included_edges:
                excluded_edge_types = set(self.edge_types).difference((
                    edges[0][2] for edges in included_edges
                ))
            else:
                excluded_edge_types = []
            subgraph = self.get_path(
                selected=self.selected,
                directional=self.path_directionality.value,
                excluded_edge_types=excluded_edge_types,
                reversed_edge_types=self.edge_type_reverser.value,
            )
            if subgraph:
                self.diagram.graph = subgraph
            else:
                self.log.warning(
                    "Could not find path between " 
                    f"""{" and ".join(self.selected)}, with directionality """
                    f"""{"not" if not self.path_directionality else ""} """ 
                    "enforced."
                )
            return
        elif button is self.filter_by_dist:
            raise NotImplementedError("Need to implement this!")

        self.diagram.graph = self.filter(
            nodes=self.selected_by_type_node_ids,
            edges=self.selected_by_type_edge_ids,
        )

        # TODO: look into adding a refresh, e.g.,
        # self.diagram.elk_app.refresh()

    @trt.observe("selected")
    def _update_based_on_selection(self, *_):
        selected = self.selected
        self.filter_to_path.disabled = (
            len(selected) != 2 or
            not all(isinstance(n, str) for n in selected)
        )
        self.filter_by_dist.disabled = not selected

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
            "Nodes": ipyw.VBox([
                ipyw.Label("Select by Type:"),
                self.node_type_selector,
            ]),
            "Edges": ipyw.VBox([
                ipyw.Label("Select by Type:"),
                self.edge_type_selector,
                ipyw.Label("Reverse by Type:"),
                self.edge_type_reverser,
            ]),
            "Filter": ipyw.VBox([
                ipyw.Label("Shortest Path:"),
                ipyw.HBox([self.filter_to_path, self.path_directionality]),
                ipyw.Label("Distance:"),
                ipyw.HBox([self.filter_by_dist, self.max_distance]),
            ]),
        })

        buttons = [*diagram.toolbar_buttons]
        buttons += [self.update_diagram]

        with diagram.hold_trait_notifications():
            diagram.toolbar_accordion = accordion
            diagram.toolbar_buttons = buttons
