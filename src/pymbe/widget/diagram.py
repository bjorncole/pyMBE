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


def a_part(data: dict, width=220):
    part = Part(data=data, identifier=data["@id"], width=width)
    value = data.get("value", None)
    if value is not None:
        name = value
    else:
        name = (
            data.get("name", None)
            or data["@id"]
        )
    part.title = Compartment(headings=[
        f"""«{data["@type"]}»""",
        f"""{name}""",
    ])
    # TODO: add properties
    return part

def a_circle_arrow_endpoint(r=6, closed=False):
    return conn.ConnectorDef(
        children=[
            conn.Circle(x=r * 1 / 6, y=0, radius=r / 5),
            conn.Path.from_list([(r, -r / 2), (r / 2, 0), (r, r / 2)],
                           closed=closed),
        ],
        correction=conn.Point(-1, 0),
        offset=conn.Point(-r * 2 / 3, 0),
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
        offset=conn.Point(-r * 2 / 3, 0),
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
        offset=conn.Point(-r * 2 / 3, 0),
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
    source: RelationEnd = None
    target: RelationEnd = None
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
    pass


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
class FeatureType(Edge):
    shape_end: ty.ClassVar[str] = "feature_typed"


EDGE_MAP = {
    "FeatureType": FeatureType,
    "Subsetting": Subsetting,
    "Superclassing": Generalization,
    "OwnedBy": OwnedBy,
    # TODO: review and map the rest of the edge types
}

DEFAULT_EDGE = DirectedAssociation


@element
class Diagram(Partition):
    """An elk diagram."""

    # TODO flesh out ideas of encapsulating diagram defs / styles / elements
    defs: ty.ClassVar[ty.Dict[str, Def]] = {
        "composition": conn.Rhomb(r=4),
        "aggregation": conn.Rhomb(r=4),
        "containment": conn.Containment(r=4),
        "directed_association": conn.StraightArrow(r=4),
        "generalization": conn.StraightArrow(r=4, closed=True),
        "subsetting": a_circle_arrow_endpoint(r=8, closed=False),
        "feature_typed": a_feature_typing_endpoint(r=8, closed=True),
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
        " .internal > .elknode": {
            "stroke": "transparent",
            "fill": "transparent",
        },
        # Necessary for having the viewport use the whole vertical height
        " .lm-Widget.jp-ElkView .sprotty > .sprotty-root > svg.sprotty-graph": {"height": "unset!important"}
    }
    default_edge: ty.Type[Edge] = field(default=DirectedAssociation)


class SysML2ElkDiagram(ipyw.HBox):
    """A SysML v2 Diagram"""

    elk_app: ipyelk.Elk = trt.Instance(ipyelk.Elk)
    elk_diagram: Diagram = trt.Instance(Diagram, args=())
    elk_layout: ipyelk.nx.XELKTypedLayout() = trt.Instance(
        ipyelk.nx.XELKTypedLayout,
        kw=dict(selected_index=None),  # makes layout start collapsed
    )
    elk_transformer: ipyelk.nx.XELK = trt.Instance(ipyelk.nx.XELK)
    graph: nx.Graph = trt.Instance(nx.Graph, args=())

    parts: dict = trt.Dict()

    style: dict = trt.Dict(kw={
        " text.elklabel.node_type_label": {
            "font-style": "italic",
        },
        " parents": {
            "org.eclipse.elk.direction": "UP",
            "org.eclipse.elk.nodeLabels.placement": "H_CENTER V_TOP INSIDE",
        },
    })

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        return [
            ipyw.VBox([self.elk_app], layout=dict(height="100%", width="80%")),
            ipyw.VBox([self.elk_layout], layout=dict(height="100%", width="20%")),
        ]

    @trt.validate("layout")
    def _validate_layout(self, proposal):
        layout = proposal.value
        layout.height = "60vh"
        return layout

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
                height="100%",
                min_height="600px",
                width="100%",
            ),
        )
        elk_app.layout.flex = "1"
        return elk_app

    @trt.observe("elk_layout")
    def _update_observers_for_layout(self, change: trt.Bunch):
        if change.old not in (None, trt.Undefined):
            change.old.unobserve(self._element_type_opt_change)
            del change.old
        change.new.observe(self._element_type_opt_change, "value")

    @trt.observe("graph")
    def _update_nodes(self, change: trt.Bunch):
        if change.old not in (None, trt.Undefined):
            old = change.old
            del old
        self.parts = {
            id_: a_part(node_data)
            for id_, node_data in self.graph.nodes.items()
            if node_data
        }
        diagram = Diagram()
        for (source, target, type_), edge in self.graph.edges.items():
            if source not in self.parts:
                self.log.warn(
                    f"Could not map source: {source} in '{type_}' with {target}"
                )
                continue
            if target not in self.parts:
                self.log.warn(
                    f"Could not map target: {target} in '{type_}' with {source}"
                )
                continue
            edge = diagram.add_edge(
                source=self.parts[source],
                target=self.parts[target],
                cls=EDGE_MAP.get(type_, DEFAULT_EDGE),
            )
            edge.labels.append(Label(text=type_))
        diagram.defs = {**diagram.defs}
        self.elk_diagram = diagram

    @trt.observe("elk_diagram")
    def _update_app(self, *_):
        self.elk_app.transformer.source = Compound()(self.elk_diagram)
        self.elk_app.style = self.elk_diagram.style
        self.elk_app.diagram.defs = self.elk_diagram.defs

        # _ = node_data.pop("@context", None)
        # node_data["id"] = id_
        # type_label = [ElkLabel(
        #     id=f"""type_label_for_{id_}""",
        #     text=f"""«{node_data["@type"]}»""",
        #     properties={
        #         "cssClasses": "node_type_label",
        #     },
        # )] if "@type" in node_data else []
        # node_data["labels"] = type_label + [
        #     node_data.get("name", node_data.get("id"))]

    def _update_diagram_layout_(self, *_):
        self.elk_app.transformer.layouts = self.elk_layout.value
        self.elk_app.refresh()
