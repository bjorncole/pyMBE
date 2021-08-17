import ipywidgets as ipyw
import traitlets as trt
from wxyz.lab import DockBox, DockPop

from .client import SysML2ClientWidget
from .containment import ContainmentTree
from .diagram import M0Viewer, M1Viewer
from .inspector import ElementInspector


@ipyw.register
class UI(DockBox):
    """A user interface for the integrated widget"""

    # buttons
    pop_log_out: ipyw.Button = trt.Instance(ipyw.Button)

    # widgets
    client: SysML2ClientWidget = trt.Instance(SysML2ClientWidget)
    tree: ContainmentTree = trt.Instance(ContainmentTree, args=())
    inspector: ElementInspector = trt.Instance(ElementInspector, args=())
    m0_viewer: M0Viewer = trt.Instance(M0Viewer, args=())
    m1_viewer: M1Viewer = trt.Instance(M1Viewer, args=())

    # links
    lpg_links: list = trt.List()
    model_links: list = trt.List()
    selector_links: list = trt.List()

    # config parameters
    diagram_height: int = trt.Int(default_value=65, min=25, max=100)

    log_out = ipyw.Output()

    def __init__(self, host_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "SysML Model"

        self.client = SysML2ClientWidget(host_url=host_url)

        self.children = [
            self.client,
            self.tree,
            self.inspector,
            self.m1_viewer,
            self.m0_viewer,
        ]

        self.dock_layout = dict(
            type="split-area",
            orientation="vertical",
            children=[
                dict(type="tab-area", widgets=[0], currentIndex=0),
                dict(
                    type="split-area",
                    orientation="horizontal",
                    children=[
                        dict(type="tab-area", widgets=[1], currentIndex=0),
                        dict(
                            type="tab-area",
                            widgets=[2, 3, 4],
                            currentIndex=0,
                        ),
                    ],
                    sizes=[0.22, 0.78],
                ),
            ],
            sizes=[0.20, 0.80],
        )

        # TODO: find a way to avoid doing these three lines
        self.client._set_layout()
        self.tree.layout.overflow_y = "auto"
        self._update_diagram_height()

        all_widgets = self.tree, self.inspector, self.m1_viewer, self.m0_viewer

        for widget in all_widgets:
            widget.log_out = self.log_out

        self.model_links = [
            trt.link(
                (self.client, "model"),
                (widget, "model"),
            )
            for widget in all_widgets
        ]
        self.selector_links = [
            trt.link(
                (self.tree, "selected"),
                (widget, "selected"),
            )
            for widget in all_widgets[1:]
        ]
        self.lpg_links = [
            trt.link(
                (self.m1_viewer, "lpg"),
                (self.m0_viewer, "lpg"),
            )
        ]

    @trt.default("pop_log_out")
    def _make_pop_log_out_button(self):
        button = ipyw.Button(
            description="",
            icon="book",
            tooltip="Pop Log",
        )
        button.on_click(self._pop_log_out)
        return button

    @trt.observe("diagram_height")
    def _update_diagram_height(self, *_):
        self.m0_viewer.layout.height = f"{self.diagram_height}vh"
        self.m1_viewer.layout.height = f"{self.diagram_height}vh"

    @classmethod
    def new(cls, host_url: str) -> DockPop:
        return DockPop([cls(host_url=host_url)], description="SysML Model")

    def _pop_log_out(self):
        DockPop([self.log_out], mode="split-right")
