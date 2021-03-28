from collections import Counter
from copy import deepcopy

from IPython.display import JSON, display

import ipytree as ipyt
import ipywidgets as ipyw
import traitlets as trt

from ..client import SysML2Client


__all__ = ("ElementDetails", "SysML2ClientWidget")


class SysML2ClientWidget(SysML2Client, ipyw.VBox):
    """An ipywidget to interact with a SysML v2 API."""

    _WIDE_WIDGET_MAX_WIDTH = "32rem"
    _WIDE_WIDGET_WIDTH = "99%"

    host_url_input = trt.Instance(ipyw.Text)
    host_port_input = trt.Instance(ipyw.IntText)
    project_selector = trt.Instance(ipyw.Dropdown)
    commit_selector = trt.Instance(ipyw.Dropdown)
    download_elements = trt.Instance(ipyw.Button)
    progress_bar = trt.Instance(ipyw.IntProgress)

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        return [
            ipyw.HTML("<h1>SysML2 Remote Service</h1>"),
            ipyw.HBox([
                ipyw.VBox([
                    self.host_url_input,
                ],
                    layout=ipyw.Layout(
                        max_width=self._WIDE_WIDGET_MAX_WIDTH,
                        width=self._WIDE_WIDGET_WIDTH,
                    ),
                ),
                self.host_port_input,
            ]),
            ipyw.HBox([
                ipyw.VBox([
                    self.project_selector,
                    self.commit_selector,
                ],
                    layout=ipyw.Layout(
                        max_width=self._WIDE_WIDGET_MAX_WIDTH,
                        width=self._WIDE_WIDGET_WIDTH,
                    ),
                ),
                self.download_elements,
            ]),
            self.progress_bar,
        ]

    @trt.default("host_url_input")
    def _make_host_url_input(self):
        input_box = ipyw.Text(
            default_value=self.host_url,
            layout=ipyw.Layout(
                max_width=self._WIDE_WIDGET_MAX_WIDTH,
                width="99%",
            ),
        )
        trt.link(
            (self, "host_url"),
            (input_box, "value"),
        )
        return input_box

    @trt.default("host_port_input")
    def _make_host_port_input(self):
        input_box = ipyw.IntText(
            default_value=self.host_port,
            min=1,
            max=65535,
            layout=ipyw.Layout(
                max_width="6rem",
                width="15%",
            ),
        )
        trt.link(
            (self, "host_port"),
            (input_box, "value"),
        )
        return input_box

    @trt.default("project_selector")
    def _make_project_selector(self):
        selector = ipyw.Dropdown(
            descriptor="Projects",
            options=self._get_project_options(),
            layout=ipyw.Layout(
                max_width=self._WIDE_WIDGET_MAX_WIDTH,
                width="99%",
            ),
        )
        trt.link((selector, "value"), (self, "selected_project"))
        return selector

    @trt.default("commit_selector")
    def _make_commit_selector(self):
        selector = ipyw.Dropdown(
            descriptor="Commits",
            options=self._get_commit_options(),
            layout=ipyw.Layout(
                max_width=self._WIDE_WIDGET_MAX_WIDTH,
                width="99%",
            ),
        )
        trt.link((selector, "value"), (self, "selected_commit"))
        return selector

    @trt.default("download_elements")
    def _make_download_elements_button(self):
        button = ipyw.Button(
            icon="cloud-download",
            tooltip="Fetch elements from remote host.",
            layout=ipyw.Layout(
                height="95%",
                max_width="6rem",
                width="15%",
            ),
        )
        button.on_click(self._download_elements)
        return button

    @trt.default("progress_bar")
    def _make_progress_bar(self):
        return ipyw.IntProgress(
            description="Loading:",
            min=0,
            max=4,
            step=1,
            value=0,
            layout=ipyw.Layout(
                max_width="36rem",
                visibility="hidden",
                width="99%",
            ),
        )

    @trt.observe("_api_configuration")
    def _update_apis(self, *_):
        self.project_selector.options = self._get_project_options()

    @trt.observe("selected_project")
    def _update_commit_options(self, *_):
        self.commit_selector.options = self._get_commit_options()

    def _download_elements(self, *_):
        progress = self.progress_bar
        progress.value = 0
        progress.layout.visibility = "visible"

        progress.value += 1

        super()._download_elements()
        progress.value += 1

        progress.value = progress.max
        progress.layout.visibility = "hidden"

    def _get_project_options(self):
        project_name_instances = Counter(
            project["name"]
            for project in self.projects.values()
        )

        return {
            data["name"] + (
                f""" ({data["created"].strftime("%Y-%m-%d %H:%M:%S")})"""
                if project_name_instances[data["name"]] > 1
                else ""
            ): id_
            for id_, data in sorted(
                self.projects.items(),
                key=lambda x: x[1]["name"],
            )
        }

    def _get_commit_options(self):
        # TODO: add more info about the commit when API provides it
        return [
            commit.id
            for commit in self._commits_api.get_commits_by_project(
                self.selected_project
            )
        ]


class Element(ipyt.Node):
    _identifier = trt.Unicode()
    _owner = trt.Unicode("self", allow_none=True)
    _type = trt.Unicode()
    _data = trt.Dict()


class ElementDetails(ipyw.HBox):

    FILTER_KEYS = ("@context",)

    element_data = trt.Instance(ipyw.Output, args=())
    nodes = trt.Dict(kw={})
    selected = trt.Unicode()
    tree = trt.Instance(ipyt.Tree)

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        return [
            self.tree,
            self.element_data,
        ]

    @trt.validate("layout")
    def _validate_layout(self, proposal):
        layout = proposal.value
        layout.grid_template_columns = "repeat(2, 500px)"
        layout.height = "450px"
        return layout

    @trt.default("tree")
    def _make_tree(self) -> ipyt.Tree:
        tree = ipyt.Tree(
            multiple_selection=False,
            layout=ipyw.Layout(width="45%")
        )
        tree.observe(self._update_selected, "selected_nodes")
        return tree

    @trt.default("element_data")
    def _make_element_data(self) -> ipyw.Output:
        element_data = ipyw.Output(
            layout=ipyw.Layout(width="45%")
        )
        return element_data

    @trt.observe("tree")
    def _update_selected_node_observer(self, change: trt.Bunch = None):
        change = change or {}
        if change.get("old"):
            change.old.unobserve(self._update_selected)
            del change.old
        self.tree.observe(self._update_selected, "selected_nodes")

    @trt.observe("selected")
    def _update_details(self, *_):
        data = self.element_data
        with data:
            data.clear_output()
            display(JSON(self.selected_data))

    def _update_selected(self, *_):
        if not self.tree.selected_nodes:
            self.selected_element = ""
            return
        self.selected = self.tree.selected_nodes[0]._identifier

    @property
    def selected_data(self):
        data = deepcopy(getattr(
            self.nodes.get(self.selected, None),
            "_data",
            {},
        ))
        for key in self.FILTER_KEYS:
            data.pop(key, None)
        return data

    def _clear_tree(self):
        tree = self.tree
        for node in tree.nodes:
            tree.remove_node(node)

    def update(self, elements: dict):
        self.nodes = {
            element_id: Element(
                name=(
                    element["name"]
                    or f"""«{element["@type"]}: {element_id}»"""
                ),
                _identifier=element["identifier"],
                _type=element["@type"],
                _owner=(element["owner"] or {}).get("@id", None),
                _data=element,
            )
            for element_id, element in elements.items()
            if element.get("name", None)
            or (element["owner"] or {}).get("@id", None)
        }

    @trt.observe("nodes")
    def _update_tree(self, *_):
        self._clear_tree()
        nodes = self.nodes
        for node in nodes.values():
            owner = node._owner
            if owner is None:
                self.tree.add_node(node)
            elif owner in nodes:
                nodes[owner].add_node(node)
            else:
                owner_name = self.nodes[owner]["_data"]["qualifiedName"]
                self.log.warning(
                    f"Not including {node} because its owner "
                    f"{owner_name} does not have a name!"
                )
