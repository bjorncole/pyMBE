from collections import Counter

import ipywidgets as ipyw
import traitlets as trt

from ..client import SysML2Client


__all__ = ("ElementDetails", "SysML2ClientWidget")


class SysML2ClientWidget(SysML2Client):
    """An ipywidget to interact with a SysML v2 API."""

    widget: ipyw.GridspecLayout = trt.Instance(ipyw.GridspecLayout)

    host_url_input = trt.Instance(ipyw.Text)
    host_port_input = trt.Instance(ipyw.IntText)
    project_selector = trt.Instance(ipyw.Dropdown)
    commit_selector = trt.Instance(ipyw.Dropdown)
    download_elements = trt.Instance(ipyw.Button)
    progress_bar = trt.Instance(ipyw.IntProgress)

    def _ipython_display_(self):
        return self.widget

    @trt.default("widget")
    def _make_widget(self) -> ipyw.GridspecLayout:
        cols = 12
        idx = cols - 1
        grid = ipyw.GridspecLayout(4, cols, width="auto", height="auto")
        grid[0, :idx] = self.host_url_input
        grid[0, idx:] = self.host_port_input
        grid[1, :idx] = self.project_selector
        grid[2, :idx] = self.commit_selector
        grid[1:3, idx:] = self.download_elements
        grid[3, :] = self.progress_bar

        for widget in (
            self.host_url_input,
            self.host_port_input,
            self.project_selector,
            self.commit_selector,
            self.download_elements,
            self.progress_bar,
        ):
            widget.layout.height="95%"
            widget.layout.width="auto"
            widget.layout.min_height=None
            widget.layout.max_height=None
            widget.layout.max_width=None
            widget.layout.min_width=None

        self.download_elements.layout.max_width = "6rem"
        self.host_port_input.layout.max_width = "6rem"
        return grid

    @trt.default("host_url_input")
    def _make_host_url_input(self):
        input_box = ipyw.Text(
            default_value=self.host_url,
            description="Server:",
            description_tooltip="The URL and port of the SysML v2 Server",
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
        )
        trt.link(
            (self, "host_port"),
            (input_box, "value"),
        )
        return input_box

    @trt.default("project_selector")
    def _make_project_selector(self):
        selector = ipyw.Dropdown(
            description="Project:",
            options=self._get_project_options(),
        )
        trt.link((selector, "value"), (self, "selected_project"))
        return selector

    @trt.default("commit_selector")
    def _make_commit_selector(self):
        selector = ipyw.Dropdown(
            description="Commit:",
            options=self._get_commit_options(),
        )
        trt.link((selector, "value"), (self, "selected_commit"))
        return selector

    @trt.default("download_elements")
    def _make_download_elements_button(self):
        button = ipyw.Button(
            icon="cloud-download",
            tooltip="Fetch elements from remote host.",
        )
        button.on_click(self._download_elements)
        return button

    @trt.default("progress_bar")
    def _make_progress_bar(self):
        progress_bar = ipyw.IntProgress(
            description="Loading:",
            min=0,
            max=4,
            step=1,
            value=0,
        )
        progress_bar.style.bar_color = "gray"
        progress_bar.layout.visibility = "hidden"
        return progress_bar

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
