import typing as ty

import ipyelk

import ipywidgets as ipyw
import traitlets as trt


DEFAULT_BUTTON_KWARGS = dict(
    description="",
    layout=dict(height="40px", width="40px"),
)

BUTTON_ICONS = {
    "Center": "crosshairs",
    "Fit": "expand-arrows-alt",
    "Toggle Collapsed": "window-maximize",
}


@ipyw.register
class Toolbar(ipyw.VBox, ipyelk.tools.toolbar.Toolbar):
    """A customized toolbar for pymbe's diagram."""

    accordion: ipyw.Accordion = trt.Instance(ipyw.Accordion)
    buttons: ipyw.HBox = trt.Instance(ipyw.HBox, args=())
    loader: ipyw.FloatProgress = trt.Instance(ipyw.FloatProgress, args=())

    update_diagram: ty.Callable = trt.Callable(allow_none=True)

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
    refresh_diagram: ipyw.Button = trt.Instance(
        ipyw.Button,
        kw=dict(
            icon="retweet",
            tooltip="Refresh Diagram",
            **DEFAULT_BUTTON_KWARGS,
        ),
    )

    filter_to_path: ipyw.Button = trt.Instance(
        ipyw.Button,
        kw=dict(
            disabled=True,
            icon="project-diagram",  # share-alt
            tooltip="Filter To Path",
            **DEFAULT_BUTTON_KWARGS,
        )
    )
    enforce_directionality: ipyw.Checkbox = trt.Instance(
        ipyw.Checkbox,
        kw=dict(
            default_value=True,
            description="Enforce Edge Directions",
        ),
    )

    filter_by_dist: ipyw.Button = trt.Instance(
        ipyw.Button,
        kw=dict(
            disabled=True,
            icon="sitemap",  # hubspot
            tooltip="Filter by Distance",
            **DEFAULT_BUTTON_KWARGS,
        )
    )
    max_distance: ipyw.IntSlider = trt.Instance(
        ipyw.IntSlider,
        kw=dict(default_valud=1, min=1, max=4),
    )

    # elk_layout: ipyelk.nx.XELKTypedLayout = trt.Instance(
    #     ipyelk.nx.XELKTypedLayout,
    #     kw=dict(selected_index=None),  # makes layout start collapsed
    # )

    max_type_selector_rows: int = trt.Int(default_value=10, min=5)

    @property
    def refresh_buttons(self):
        """These are the buttons that refresh the diagram view"""
        return (
            self.refresh_diagram,
            self.filter_to_path,
            self.filter_by_dist,
        )

    @trt.default("accordion")
    def _make_accordion(self):
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
            # "Layout": ...
        }
        titles, widgets = zip(*accordion.items())
        return ipyw.Accordion(
            _titles={
                idx: title
                for idx, title in enumerate(titles)
            },
            children=widgets,
            selected_index=None,
        )

    @trt.validate("children")
    def _validate_children(self, proposal):
        return [
            self.buttons,
            self.accordion,
            self.loader,
        ]

    @trt.validate("layout")
    def _validate_layout(self, proposal):
        layout = proposal.value
        layout.width = "auto"
        layout.visibility = "visible"
        return layout

    @trt.observe("update_diagram")
    def _update_callables(self, change: trt.Bunch):
        for button in self.refresh_buttons:
            if change.old:
                button.on_click(change.old, remove=True)
            button.on_click(change.new)

    @trt.observe("tools")
    def _update_children(self, *_):
        """Note: overwrites ipyelk.Toolbar method."""
        self.buttons.children = buttons = [
            tool.ui for tool in self.tools
            if isinstance(tool.ui, ipyw.Button)
        ] + [self.refresh_diagram, self.close_btn]
        for button in buttons:
            button.layout.height = "40px"
            button.layout.width = "40px"
            if button.description:
                button.tooltip = button.description
                button.description = ""
            if not button.icon and button.tooltip:
                icon = BUTTON_ICONS.get(button.tooltip)
                if icon:
                    button.icon = icon

        self.loader = self.get_tool(ipyelk.tools.PipelineProgressBar).ui
        self.loader.layout.width = "100%"
        self.loader.layout.visibility = "hidden"

    def get_tool(self, tool_type: ty.Type[ipyelk.Tool]) -> ipyelk.Tool:
        matches = [tool for tool in self.tools if type(tool) is tool_type]
        num_matches = len(matches)
        if num_matches > 1:
            raise ipyelk.exceptions.NotUniqueError(
                f"Found too many tools with type {tool_type}"
            )
        elif num_matches < 1:
            raise ipyelk.exceptions.NotFoundError(
                f"No tool matching type {tool_type}"
            )

        return matches[0]

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

    def update_dropdown_options(self, selector: str, options: dict):
        if selector == "nodes":
            selectors = [self.node_type_selector]
        elif selector == "edges":
            selectors = [self.edge_type_selector, self.edge_type_reverser]
        for selector in selectors:
            selector.options = options
        self._update_rows_in_multiselect(selectors=selectors)
