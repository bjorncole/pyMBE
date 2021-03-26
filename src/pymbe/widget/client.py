from collections import Counter

import ipywidgets as ipyw
import traitlets as trt

from ..client import SysML2Client


class SysML2ClientWidget(SysML2Client, ipyw.VBox):
    """An ipywidget to interact with a SysML v2 API."""
    
    host_url_input = trt.Instance(ipyw.Text)
    host_port_input = trt.Instance(ipyw.IntText)
    project_selector = trt.Instance(ipyw.Dropdown)
    commit_selector = trt.Instance(ipyw.Dropdown)
    download_elements = trt.Instance(ipyw.Button)
    progress_bar = trt.Instance(ipyw.IntProgress, kw=dict(
        description="Loading:",
        min=0,
        max=6,
        step=1,
        value=0,
        layout=ipyw.Layout(
            max_width = "30rem",
            visibility="hidden",
            width = "80%",
        ),
    ))
    edge_type_selector = trt.Instance(ipyw.SelectMultiple, args=tuple())
    node_type_selector = trt.Instance(ipyw.SelectMultiple, args=tuple())

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        return [
            ipyw.HTML("<h1>SysML2 Remote Service</h1>"),
            ipyw.HBox([self.host_url_input, self.host_port_input]),
            ipyw.HBox([
                ipyw.VBox([
                    self.project_selector,
                    self.commit_selector,
                    self.progress_bar,
                ], layout=ipyw.Layout(width="80%", max_width="32rem")),
                self.download_elements,
            ]),
            ipyw.HBox([
                ipyw.VBox([
                    ipyw.HTML("<h2>Relationship Types</h2>"),
                    self.edge_type_selector,
                ]),
                ipyw.VBox([
                    ipyw.HTML("<h2>Non-Relationship Types</h2>"),
                    self.node_type_selector,
                ]),
            ]),
        ]
    
    @trt.default("host_url_input")
    def _make_host_url_input(self):
        input_box = ipyw.Text(default_value=self.host_url)
        trt.link(
            (self, "host_url"),
            (input_box, "value"),
        )
        layout = input_box.layout
        layout.width = "80%"
        layout.max_width = "30rem"
        return input_box

    @trt.default("host_port_input")
    def _make_host_port_input(self):
        input_box = ipyw.IntText(
            default_value=self.host_port,
            min=1,
            max=65535,
        )
        trt.link(
            (self, "host_port"),
            (input_box, "value"),
        )
        layout = input_box.layout
        layout.width = "15%"
        layout.max_width = "6rem"
        return input_box

    @trt.default("project_selector")
    def _make_project_selector(self):
        selector = ipyw.Dropdown(
            descriptor="Projects",
            options=self._get_project_options(),
        )
        selector.observe(self._update_commit_options, "value")
        selector.layout.width = "99%"
        selector.layout.max_width = "30rem"
        return selector

    @trt.default("commit_selector")
    def _make_commit_selector(self):
        selector = ipyw.Dropdown(
            descriptor="Commits",
            options=self._get_commit_options(),
        )
        selector.observe(self._update_elements, "value")
        selector.layout.width = "99%"
        selector.layout.max_width = "30rem"
        return selector

    @trt.default("download_elements")
    def _make_download_elements_button(self):
        button = ipyw.Button(
            icon="cloud-download",
            tooltip="Fetch elements from remote host.",
        )
        button.on_click(self._download_elements)
        layout = button.layout
        layout.height, layout.width = "90%", "15%"
        layout.max_width = "6rem"
        return button

    @trt.observe("elements_by_type")
    def _updated_type_selector_options(self, *_):
        self.edge_type_selector.options = {
            f"{element_type} [{len(elements)}]": elements
            for element_type, elements in sorted(self.elements_by_type.items())
            if element_type in self.relationship_types
        }
        self.node_type_selector.options = {
            f"{element_type} [{len(elements)}]": elements
            for element_type, elements in sorted(self.elements_by_type.items())
            if element_type not in self.relationship_types
        }

    @property
    def selected_project_id(self):
        return self.project_selector.value

    @property
    def selected_commit_id(self):
        return self.commit_selector.value

    def _download_elements(self, *_):
        progress = self.progress_bar
        progress.value = 0
        progress.layout.visibility = "visible"

        progress.value += 1

        elements = self._get_elements_from_server()
        progress.value += 1

        self._update_elements(elements=elements)
        progress.value += 1

        self.lpg.update(client=self)
        progress.value += 1

        self.rdf.update(client=self)
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
                self.selected_project_id
            )
        ]

    def _update_commit_options(self, *_):
        self.commit_selector.options = self._get_commit_options()

    @property
    def selected_elements_by_type(self):
        element_ids = (
            sum(map(list, self.node_type_selector.value), [])
            + sum(map(list, self.edge_type_selector.value), [])
        )
        return [
            self.elements_by_id[id_]
            for id_ in element_ids
        ]
