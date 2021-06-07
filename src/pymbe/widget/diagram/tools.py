import typing as ty

import ipyelk

import ipywidgets as ipyw
import traitlets as trt


BUTTON_MAP = {
    "Fit": "",
    "Center": "crosshairs",
    "Toggle Collapsed": "expand",
}


@ipyw.register
class Toolbar(ipyw.VBox, ipyelk.tools.toolbar.Toolbar):

    accordion: ty.Dict[str, ipyw.Widget] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Instance(ipyw.Widget),
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
    projection_selector: ipyw.Dropdown = trt.Instance(ipyw.Dropdown, args=())
    update_diagram: ipyw.Button = trt.Instance(ipyw.Button)

    filter_to_path: ipyw.Button = trt.Instance(ipyw.Button)
    enforce_directionality: ipyw.Checkbox = trt.Instance(
        ipyw.Checkbox,
        kw=dict(
            default_value=True,
            description="Enforce Edge Directions",
        ),
    )

    filter_by_dist: ipyw.Button = trt.Instance(ipyw.Button)
    max_distance: ipyw.IntSlider = trt.Instance(
        ipyw.IntSlider,
        kw=dict(default_valud=1, min=1, max=4),
    )

    elk_layout: ipyelk.nx.XELKTypedLayout = trt.Instance(
        ipyelk.nx.XELKTypedLayout,
        kw=dict(selected_index=None),  # makes layout start collapsed
    )

    max_type_selector_rows: int = trt.Int(default_value=10, min=5)

    @trt.default("update_diagram")
    def _make_update_diagram_button(self) -> ipyw.Button:
        button = ipyw.Button(
            description="",
            icon="retweet",
            tooltip="Update diagram",
            layout=dict(height="40px", width="40px")
        )
        button.on_click(self._on_button_click)
        return button

    @trt.default("filter_to_path")
    def _make_filter_to_path_button(self) -> ipyw.Button:
        button = ipyw.Button(
            description="",
            disabled=True,
            icon="project-diagram",  # share-alt
            layout=dict(height="40px", width="40px"),
            tooltip="Filter To Path",
        )
        button.on_click(self._on_button_click)
        return button

    @trt.default("filter_by_dist")
    def _make_filter_by_dist_button(self) -> ipyw.Button:
        button = ipyw.Button(
            description="",
            disabled=True,
            icon="sitemap",  # hubspot
            layout=dict(height="40px", width="40px"),
            tooltip="Filter by Distance",
        )
        button.on_click(self._on_button_click)
        return button

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        for child in children:
            icon = BUTTON_MAP.get(child.description)
            if not (isinstance(child, ipyw.Button) and icon):
                continue
            child.description = ""
            child.icon = icon
        return children

    @trt.validate("layout")
    def _validate_layout(self, proposal):
        layout = proposal.value
        layout.width = "auto"
        return layout

    def update_options(self, selector: str, options: dict):
        if selector == "nodes":
            selectors = [self.node_type_selector]
        elif selector == "edges":
            selectors = [self.edge_type_selector, self.edge_type_reverser]
        for selector in selectors:
            selector.options = options
        self._update_rows_in_multiselect(selectors=selectors)

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

    def _update_diagram_toolbar(self):
        # Add elements to the elk_app toolbar
        accordion = {
            "Projection": self.projection_selector,
            "Type Filter": ipyw.Accordion(
                _titles={0: "Node Types", 1: "Edge Types"},
                children=[
                    self.node_type_selector,
                    self.edge_type_selector,
                ],
                selected_index=None,
            ),
            "Reverse Edges": self.edge_type_reverser,
            "Explore": ipyw.VBox([
                self.enforce_directionality,
                ipyw.Label("Shortest Path:"),
                ipyw.HBox([self.filter_to_path]),
                ipyw.Label("Distance:"),
                ipyw.HBox([self.filter_by_dist, self.max_distance]),
            ]),
        }
        accordion.update({**self.toolbar_accordion})
        buttons = [*self.toolbar_buttons] + [self.update_diagram]

        with self.hold_trait_notifications():
            self.toolbar_accordion = accordion
            self.toolbar_buttons = buttons

    def _make_command_palette(self) -> ipyw.VBox:
        titles, widgets = zip(*self.toolbar_accordion.items())
        titles = {
            idx: title
            for idx, title in enumerate(titles)
        }
        return ipyw.VBox(
            [
                ipyw.HBox(self.toolbar_buttons),
                ipyw.Accordion(
                    _titles=titles,
                    children=widgets,
                    selected_index=None,
                ),
            ],
        )
