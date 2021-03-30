from collections import Counter

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
