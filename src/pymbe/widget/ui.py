import ipywidgets as ipyw
import traitlets as trt
from wxyz.lab import DockBox, DockPop

from pymbe.widget.diagram.widget import DiagramWidget

from .client import SysML2ClientWidget
from .containment import ContainmentTree
from .inspector import ElementInspector
from .interpretation import Interpreter


@ipyw.register
class UI(DockBox):
    """A user interface for the integrated widget"""

    # widgets
    client: SysML2ClientWidget = trt.Instance(SysML2ClientWidget)
    tree: ContainmentTree = trt.Instance(ContainmentTree, args=())
    inspector: ElementInspector = trt.Instance(ElementInspector, args=())
    # interpreter: Interpreter = trt.Instance(Interpreter, args=())
    diagram: DiagramWidget = trt.Instance(DiagramWidget, args=())

    # links
    model_links: list = trt.List()
    selector_links: list = trt.List()

    # config parameters
    diagram_height: int = trt.Int(default_value=65, min=25, max=100)

    log_out = ipyw.Output()

    def __init__(self, host_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "SysML Model"

        self.client = SysML2ClientWidget(host_url=host_url)
        # self.interpreter.lpg = self.diagram.lpg

        self.children = [
            self.client,
            self.tree,
            self.inspector,
            self.diagram,
            # self.interpreter,
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
                            widgets=[2, 3],  # 4],  TODO: bring this back
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

        all_widgets = self.tree, self.inspector, self.diagram  # , self.interpreter)

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

    @trt.observe("diagram_height")
    def _update_diagram_height(self, *_):
        self.diagram.layout.height = f"{self.diagram_height}vh"

    @classmethod
    def new(cls, host_url: str) -> DockPop:
        return DockPop([cls(host_url=host_url)], description="SysML Model")
