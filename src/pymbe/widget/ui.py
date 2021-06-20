import ipywidgets as ipyw
import traitlets as trt

from wxyz.lab import DockPop, DockBox

from .client import SysML2ClientWidget
from .containment import ContainmentTree
from .inspector import ElementInspector
from .interpretation import Interpreter
from pymbe.widget.diagram.widget import SysML2LPGWidget


@ipyw.register
class UI(DockBox):
    """A user interface for the integrated widget"""

    # widgets
    client: SysML2ClientWidget = trt.Instance(SysML2ClientWidget)
    tree: ContainmentTree = trt.Instance(ContainmentTree, args=())
    inspector: ElementInspector = trt.Instance(ElementInspector, args=())
    interpreter: Interpreter = trt.Instance(Interpreter, args=())
    lpg: SysML2LPGWidget = trt.Instance(SysML2LPGWidget, args=())

    # links
    data_links: list = trt.List()
    selector_links: list = trt.List()

    # config parameters
    lpg_height: int = trt.Int(default_value=65, min=25, max=100)

    def __init__(self, host_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "SysML Model"

        self.client = SysML2ClientWidget(host_url=host_url)
        # self.interpreter.lpg = self.lpg

        self.children = [
            self.client,
            self.tree,
            self.inspector,
            self.lpg,
            #self.interpreter,
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
                            widgets=[2, 3],# 4],
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
        self._update_lpg_height()

        self.data_links = [
            trt.link(
                (self.client, "elements_by_id"),
                (widget, "elements_by_id"),
            )
            for widget in (self.tree, self.inspector, self.lpg)
        ]
        self.selector_links = [
            trt.link(
                (self.tree, "selected"),
                (widget, "selected"),
            )
            for widget in (self.inspector, self.lpg) #, self.interpreter)
        ]

    @trt.observe("lpg_height")
    def _update_lpg_height(self, *_):
        self.lpg.layout.height = f"{self.lpg_height}vh"

    @classmethod
    def new(cls, host_url: str) -> DockPop:
        return DockPop([cls(host_url=host_url)], description="SysML Model")
