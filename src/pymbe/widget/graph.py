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

    max_type_selector_rows: int = trt.Int(default_value=10, min=5)

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
        if self.selector_link:
            self.selector_link.unlink()
        self.selector_link = trt.link(
            (self, "selected"),
            (self.diagram, "selected"),
        )

    @trt.observe("nodes_by_type")
    def _update_node_type_selector_options(self, *_):
        self.node_type_selector.options = {
            f"{node_type} [{len(nodes)}]": nodes
            for node_type, nodes in sorted(self.nodes_by_type.items())
        }
        self._update_rows_in_multiselect(
            selectors=[self.node_type_selector],
        )

    @trt.observe("edges_by_type")
    def _update_edge_type_selector_options(self, *_):
        self.edge_type_selector.options = {
            f"{edge_type} [{len(edges)}]": edges
            for edge_type, edges in sorted(self.edges_by_type.items())
            if edge_type in self.edge_types
        }

        self.edge_type_reverser.options = self.edge_types
        self._update_rows_in_multiselect(
            selectors=[self.edge_type_selector, self.edge_type_reverser],
        )

    @trt.observe("max_type_selector_rows")
    def _update_rows_in_multiselect(
        self,
        *_,
        selectors: list = None,
    ):
        if not selectors:
            selectors = [
                getattr(self, item)
                for item in dir(self)
                if isinstance(getattr(self, item), ipyw.SelectMultiple)
            ]
        for selector in selectors:
            selector.rows = min(
                self.max_type_selector_rows,
                len(selector.options)
            )

    @trt.observe("graph")
    def _on_graph_update(self, *_):
        self.diagram.graph = self.graph

    @trt.observe("selected")
    def _update_based_on_selection(self, *_):
        selected = self.selected
        self.filter_to_path.disabled = (
            len(selected) != 2 or
            not all(isinstance(n, str) for n in selected)
        )
        self.filter_by_dist.disabled = not selected

    @property
    def excluded_edge_types(self):
        included_edges = self.edge_type_selector.value
        if not included_edges:
            return []

        return set(self.edge_types).difference((
                edges[0][2] for edges in included_edges
            ))

    @property
    def excluded_node_types(self):
        included_nodes = self.node_type_selector.value
        if not included_nodes:
            return []

        return set(self.node_types).difference((
            self.graph.nodes[nodes[0]]["@type"] for nodes in included_nodes
        ))

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

    def _update_diagram_graph(self, button=None):
        directed = self.path_directionality.value
        if self.edge_type_reverser.value and not directed:
            raise ValueError(
                f"Reversing edge types: {reversed_edge_types} makes no "
                "sense since directional is False")

        new_graph = self._get_subgraph(
            excluded_edge_types=self.excluded_edge_types,
            excluded_node_types=self.excluded_node_types,
            reversed_edge_types=self.edge_type_reverser.value,
        )

        if button is self.filter_to_path:
            source, target = self.selected
            new_graph = self.get_path_graph(
                graph=new_graph,
                source=source,
                target=target,
                directed=directed,
            )
            if not new_graph:
                self.filter_to_path.disabled = True
                self.log.warning(
                    "Could not find path between " 
                    f"""{" and ".join(self.selected)}, with directionality """
                    f"""{"not" if not self.path_directionality else ""} """ 
                    "enforced."
                )
        elif button is self.filter_by_dist:
            new_graph = self.get_spanning_graph(
                graph=new_graph,
                seeds=self.selected,
                max_distance=self.max_distance.value,
                directed=directed,
            )
            if not new_graph:
                self.filter_by_dist.disabled = True
                self.log.warning(
                    "Could not find a spanning graph of distance "
                    f"{self.max_distance.value} from these seeds: " 
                    f"{self.selected}."
                )

        self.diagram.graph = new_graph
        # self.diagram.elk_app.refresh()
        self.diagram.elk_app.diagram.fit()

    def _update_diagram_toolbar(self):
        # Append elements to the elk_app toolbar
        diagram = self.diagram
        accordion = {**diagram.toolbar_accordion}

        sub_accordion = ipyw.Accordion(
            _titles={0: "Node Types", 1: "Edge Types"},
            children=[
                self.node_type_selector,
                self.edge_type_selector,
            ],
            selected_index=None,
        )
        accordion.update({
            # TODO: enable this after the functionality is complete
            # "Reverse Edges": self.edge_type_reverser,
            "Filter": ipyw.VBox([
                self.path_directionality,
                ipyw.Label("Shortest Path:"),
                ipyw.HBox([self.filter_to_path, ]),
                ipyw.Label("Distance:"),
                ipyw.HBox([self.filter_by_dist, self.max_distance]),
                sub_accordion,
            ]),
        })

        buttons = [*diagram.toolbar_buttons]
        buttons += [self.update_diagram]

        with diagram.hold_trait_notifications():
            diagram.toolbar_accordion = accordion
            diagram.toolbar_buttons = buttons
