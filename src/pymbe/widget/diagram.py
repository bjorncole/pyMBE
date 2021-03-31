from dataclasses import field
from enum import Enum

import ipywidgets as ipyw
import networkx as nx
import traitlets as trt
import typing as ty

import ipyelk
import ipyelk.nx
import ipyelk.contrib.shapes.connectors as conn

from ipyelk.contrib.elements import (
    Compartment,
    Compound,
    Edge,
    Label,
    Partition,
    Record,
    element,
    elements,
)
from ipyelk.diagram.elk_model import ElkLabel
from ipyelk.diagram.symbol import Def
from ipyelk.tools import tools as elk_tools


def a_part(data: dict, width=220):
    value = data.get("value", None)
    if value is not None:
        name = value
        if isinstance(value, (bool, float, int)):
            width = int(0.5 * width)
    else:
        name = (
            data.get("name", None)
            or data["@id"]
        )
    part = Part(data=data, identifier=data["@id"], width=width)
    part.title = Compartment(headings=[
        f"""«{data["@type"]}»""",
        f"""{name}""",
    ])
    # TODO: add properties
    return part


def an_arrow_endpoint(r=6, closed=False):
    return conn.ConnectorDef(
        children=[
            conn.Path.from_list(
                [(r / 2, -r / 3), (0, 0), (r / 2, r / 3)],
                closed=closed,
            ),
        ],
        correction=conn.Point(-1, 0),
        offset=conn.Point((-r / 1.75) if closed else 0, 0),
    )


def a_feature_typing_endpoint(r=6, closed=False):
    return conn.ConnectorDef(
        children=[
            conn.Circle(x=r * 4 / 5, y=r / 4, radius=r / 20),
            conn.Circle(x=r * 4 / 5, y=-r / 4, radius=r / 20),
            conn.Path.from_list(
                [(r / 2, -r / 3), (0, 0), (r / 2, r / 3)],
                closed=closed,
            ),
        ],
        correction=conn.Point(-1, 0),
        offset=conn.Point((-r / 1.75) if closed else 0, 0),
    )


def a_redefinition_endpoint(r=6, closed=False):
    return conn.ConnectorDef(
        children=[
            conn.Path.from_list([(r * 4 / 5, -r / 3), (r * 4 / 5, r / 3)]),
            conn.Path.from_list(
                [(r / 2, -r / 3), (0, 0), (r / 2, r / 3)],
                closed=closed,
            ),
        ],
        correction=conn.Point(-1, 0),
        offset=conn.Point((-r / 1.75) if closed else 0, 0),
    )


def a_subsetting_endpoint(r=6, closed=False):
    return conn.ConnectorDef(
        children=[
            conn.Circle(x=r / 5, y=0, radius=r / 5),
            conn.Path.from_list(
                [(r, -r / 2.5), (r / 2.5, 0), (r, r / 2.5)],
                closed=closed,
            ),
        ],
        correction=conn.Point(-1, 0),
        offset=conn.Point(-r if closed else (-r / 1.9), 0),
    )


class VisibilityKind(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    PACKAGE = "package"


class RelationEndKind(Enum):
    HEAD = "head"
    TAIL = "tail"


@element
class Part(Record):
    data: dict = field(default_factory=dict)
    identifier: str = ""


@element
class RelationEnd(elements.BaseElement):
    kind: RelationEndKind = None
    multiplicity: ty.Tuple[int, int] = tuple((None, None))
    name: str = None
    attributes: ty.List[str] = None


@element
class Relation(Edge):
    kind: str = "Undefined"
    source_end: RelationEnd = None
    target_end: RelationEnd = None
    display_kind: bool = True
    display_multiplicity: bool = True
    display_usage: bool = True

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)
        if self.labels:
            return

        if self.display_kind and self.kind:
            self.labels += [ElkLabel(
                text=f"«{self.kind}»",
                id=f"{self.id}_label",
            )]

        if self.display_multiplicity and self.multiplicity:
            mid = "" if None in self.multiplicity else ".."

            lower, upper = self.multiplicity

            lower = self.multiplicity[0] or "0"
            upper = self.multiplicity[1] or "*"
            self.labels += [ElkLabel(
                id=f"{self.id}_label_tail",
                text=f"{lower}{mid}{upper}",
                layoutOptions={
                    "org.eclipse.elk.edgeLabels.placement": "TAIL",
                },
            )]

        if self.display_usage and self.usage:
            self.labels += [ElkLabel(
                id=f"{self.id}_label_tail",
                text=f"{{{self.usage}}}",
                layoutOptions={
                    "org.eclipse.elk.edgeLabels.placement": "HEAD",
                },
            )]


@element
class Association(Edge):
    shape_end: ty.ClassVar[str] = "association"


@element
class Composition(Edge):
    shape_start: ty.ClassVar[str] = "composition"


@element
class Aggregation(Edge):
    shape_start: ty.ClassVar[str] = "aggregation"


@element
class Containment(Edge):
    shape_start: ty.ClassVar[str] = "containment"


@element
class OwnedBy(Edge):
    shape_end: ty.ClassVar[str] = "containment"


@element
class DirectedAssociation(Edge):
    shape_end: ty.ClassVar[str] = "directed_association"


@element
class Generalization(Edge):
    shape_end: ty.ClassVar[str] = "generalization"


@element
class Subsetting(Edge):
    shape_end: ty.ClassVar[str] = "subsetting"


@element
class FeatureTyping(Edge):
    shape_end: ty.ClassVar[str] = "feature_typing"


@element
class Redefinition(Edge):
    shape_end: ty.ClassVar[str] = "redefinition"


EDGE_MAP = {
    "FeatureTyping": FeatureTyping,
    "OwnedBy": OwnedBy,
    "Redefinition": Redefinition,
    "Subsetting": Subsetting,
    "Superclassing": Generalization,
    # TODO: review and map the rest of the edge types
}

DEFAULT_EDGE = DirectedAssociation


@element
class Diagram(Partition):
    """An elk diagram."""

    # TODO flesh out ideas of encapsulating diagram defs / styles / elements
    defs: ty.ClassVar[ty.Dict[str, Def]] = {
        "aggregation": conn.Rhomb(r=4),
        "composition": conn.Rhomb(r=4),
        "containment": conn.Containment(r=4),
        "directed_association": an_arrow_endpoint(r=10, closed=False),
        "feature_typing": a_feature_typing_endpoint(r=10, closed=True),
        "generalization": an_arrow_endpoint(r=10, closed=True),
        "redefinition": a_redefinition_endpoint(r=10, closed=True),
        "subsetting": a_subsetting_endpoint(r=10, closed=False),
    }
    style: ty.ClassVar[ty.Dict[str, Def]] = {
        # Elk Label styles for Box Titles
        " .elklabel.compartment_title_1": {
            # "font-weight": "bold",
        },
        " .elklabel.heading, .elklabel.compartment_title_2": {
            "font-weight": "bold",
        },
        # Style Arrowheads (future may try to )
        " .subsetting > .round > ellipse": {"fill": "var(--jp-elk-node-stroke)"},
        " .feature_typing > .round > ellipse": {"fill": "var(--jp-elk-node-stroke)"},
        " .internal > .elknode": {
            "stroke": "transparent",
            "fill": "transparent",
        },
        # Necessary for having the viewport use the whole vertical height
        " .lm-Widget.jp-ElkView .sprotty > .sprotty-root > svg.sprotty-graph": {"height": "unset!important"}
    }
    default_edge: ty.Type[Edge] = field(default=DirectedAssociation)


class SysML2ElkDiagram(ipyw.Box):
    """A SysML v2 Diagram"""

    elk_app: ipyelk.Elk = trt.Instance(ipyelk.Elk)
    elk_diagram: Diagram = trt.Instance(Diagram, args=())
    elk_layout: ipyelk.nx.XELKTypedLayout() = trt.Instance(
        ipyelk.nx.XELKTypedLayout,
        kw=dict(selected_index=None),  # makes layout start collapsed
    )
    elk_transformer: ipyelk.nx.XELK = trt.Instance(ipyelk.nx.XELK)
    graph: nx.Graph = trt.Instance(nx.Graph, args=())

    fit_btn: elk_tools.FitBtn = trt.Instance(elk_tools.FitBtn)
    toggle_btn: elk_tools.ToggleCollapsedBtn = trt.Instance(
        elk_tools.ToggleCollapsedBtn,
    )
    toolbar_buttons: list = trt.List(trait=trt.Instance(ipyw.Button))
    toolbar_accordion: dict = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Instance(ipyw.Widget),
    )

    style: dict = trt.Dict(kw={
        " text.elklabel.node_type_label": {
            "font-style": "italic",
        },
        " parents": {
            "org.eclipse.elk.direction": "RIGHT",
            "org.eclipse.elk.nodeLabels.placement": "H_CENTER V_TOP INSIDE",
        },
    })

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        self._update_toolbar()
        return [self.elk_app]

    @trt.default("elk_transformer")
    def _make_transformer(self) -> ipyelk.nx.XELK:
        return ipyelk.nx.XELK(
            source=(self.graph, None),
            label_key="labels",
            layouts=self.elk_layout.value,
        )

    @trt.default("elk_app")
    def _make_app(self) -> ipyelk.Elk:
        elk_app = ipyelk.Elk(
            transformer=self.elk_transformer,
            style=self.style,
            layout=dict(
                flex="1",
                height="100%",
                width="100%",
            ),
        )
        return elk_app

    @trt.default("toggle_btn")
    def _make_toggle_btn(self) -> elk_tools.ToggleCollapsedBtn:
        return elk_tools.ToggleCollapsedBtn(
            app=self.elk_app,
            description="",
            icon="compress",
            layout=dict(height="40px", width="40px"),
            tooltip="Collapse/Expand the selected elements",
        )

    @trt.default("fit_btn")
    def _make_fit_btn(self) -> elk_tools.FitBtn:
        return elk_tools.FitBtn(
            app=self.elk_app,
            description="",
            icon="expand-arrows-alt",
            layout=dict(height="40px", width="40px"),
            tooltip="Fit Diagram",
        )

    @trt.default("toolbar_buttons")
    def _make_toolbar_buttons(self):
        return [self.fit_btn, self.toggle_btn]

    @trt.default("toolbar_accordion")
    def _make_toolbar_accordion(self):
        return {
            "Layout": self.elk_layout,
        }

    @trt.observe("toolbar_buttons", "toolbar_accordion")
    def _update_toolbar(self, *_):
        self.elk_app.toolbar.commands = [self._make_command_palette()]

    @trt.observe("elk_layout")
    def _update_observers_for_layout(self, change: trt.Bunch):
        if change.old not in (None, trt.Undefined):
            change.old.unobserve(self._element_type_opt_change)
            del change.old
        change.new.observe(self._element_type_opt_change, "value")

    @trt.observe("graph")
    def _update_diagram(self, change: trt.Bunch):
        if change.old not in (None, trt.Undefined):
            old = change.old
            del old
        graph = self.graph
        parts = {
            id_: a_part(node_data)
            for id_, node_data in graph.nodes.items()
            if node_data
        }
        diagram = Diagram()
        for (source, target, type_), edge in graph.edges.items():
            if source not in parts:
                self.log.warn(
                    f"Could not map source: {source} in '{type_}' with {target}"
                )
                continue
            if target not in parts:
                self.log.warn(
                    f"Could not map target: {target} in '{type_}' with {source}"
                )
                continue
            edge = diagram.add_edge(
                source=parts[source],
                target=parts[target],
                cls=EDGE_MAP.get(type_, DEFAULT_EDGE),
            )
            edge.labels.append(Label(text=f"«{type_}»"))
        diagram.defs = {**diagram.defs}
        self.elk_diagram = diagram

    @trt.observe("elk_diagram")
    def _update_app(self, *_):
        self.elk_app.transformer.source = Compound()(self.elk_diagram)
        self.elk_app.style = self.elk_diagram.style
        self.elk_app.diagram.defs = self.elk_diagram.defs

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
                )
            ],
        )

    def _update_diagram_layout_(self, *_):
        self.elk_app.transformer.layouts = self.elk_layout.value
        self.elk_app.refresh()
