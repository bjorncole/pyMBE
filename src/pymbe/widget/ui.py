import ipywidgets as ipyw
import traitlets as trt

from wxyz.lab import DockPop, DockBox

from .client import SysML2ClientWidget
from .containment import ContainmentTree
from .inspector import ElementInspector
from .graph import SysML2LPGWidget


@ipyw.register
class UI(DockBox):
    """A user interface for the integrated widget"""

    # widgets
    client: SysML2ClientWidget = trt.Instance(
        SysML2ClientWidget,
        kw=dict(host_url="http://sysml2-sst.intercax.com"),
    )
    tree: ContainmentTree = trt.Instance(ContainmentTree, args=())
    inspector: ElementInspector = trt.Instance(ElementInspector, args=())
    lpg: SysML2LPGWidget = trt.Instance(
        SysML2LPGWidget,
        kw=dict(layout=dict(height="66vh")),
    )

    # links
    data_links: list = trt.List()
    selector_links: list = trt.List()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = "SysML Model"

        self.children = [
            self.client,
            self.tree,
            self.inspector,
            self.lpg,
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
                        dict(type="tab-area", widgets=[2, 3], currentIndex=0),
                    ],
                    sizes=[0.22, 0.78],
                ),
            ],
            sizes=[0.20, 0.80],
        )

        # TODO: find a way to avoid doing these fixes
        self.client._set_layout()
        self.tree.layout.overflow_y = "auto"

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
            for widget in (self.inspector, self.lpg)
        ]

    @classmethod
    def new(cls):
        return DockPop([cls()], description="SysML Model")
