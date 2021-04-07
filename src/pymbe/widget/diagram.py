from dataclasses import dataclass, field
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
    Mark,
    Partition,
    Record,
    element,
    elements,
)
from ipyelk.diagram.elk_model import ElkLabel
from ipyelk.diagram.symbol import Def
from ipyelk.tools import tools as elk_tools


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


@dataclass
class Mapper:
    to_map: dict = field(repr=False)
    from_map: dict = field(default=None, repr=False)

    def __repr__(self):
        return f"Mapper({len(self.to_map)} Items)"

    def __post_init__(self, *args, **kwargs):
        self.from_map = {v: k for k, v in self.to_map.items()}

    def get(self, *items):
        found = [
            self.to_map.get(item, self.from_map.get(item))
            for item in items
        ]
        return [
            item
            for item in found
            if item is not None
        ]


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
    id: str = ""


@element
class RelationEnd(elements.BaseElement):
    kind: RelationEndKind = None
    multiplicity: ty.Tuple[int, int] = tuple((None, None))
    name: str = None
    attributes: ty.List[str] = None


@element
class Relationship(Edge):

    source_end: RelationEnd = None
    target_end: RelationEnd = None
    display_kind: bool = True
    display_multiplicity: bool = True
    display_usage: bool = True

    def update(self, edge_data: dict):
        properties = self.properties
        properties["@id"] = edge_data["@id"]

        self.labels.append(Label(text=f"""«{edge_data["@type"]}»"""))

        # TODO: Add processing of relationship properties
        # if self.display_kind and self.kind:
        #     self.labels += [ElkLabel(
        #         text=f"«{self.kind}»",
        #         id=f"{self.identifier}_label",
        #     )]

        # if self.display_multiplicity and self.multiplicity:
        #     mid = "" if None in self.multiplicity else ".."

        #     lower, upper = self.multiplicity

        #     lower = self.multiplicity[0] or "0"
        #     upper = self.multiplicity[1] or "*"
        #     self.labels += [ElkLabel(
        #         id=f"{self.id}_label_tail",
        #         text=f"{lower}{mid}{upper}",
        #         layoutOptions={
        #             "org.eclipse.elk.edgeLabels.placement": "TAIL",
        #         },
        #     )]

        # if self.display_usage and self.usage:
        #     self.labels += [ElkLabel(
        #         id=f"{self.id}_label_tail",
        #         text=f"{{{self.usage}}}",
        #         layoutOptions={
        #             "org.eclipse.elk.edgeLabels.placement": "HEAD",
        #         },
        #     )]


@element
class Association(Relationship):
    shape_end: ty.ClassVar[str] = "association"


@element
class Composition(Relationship):
    shape_start: ty.ClassVar[str] = "composition"


@element
class Aggregation(Relationship):
    shape_start: ty.ClassVar[str] = "aggregation"


@element
class Containment(Relationship):
    shape_start: ty.ClassVar[str] = "containment"


@element
class OwnedBy(Relationship):
    shape_end: ty.ClassVar[str] = "containment"


@element
class DirectedAssociation(Relationship):
    shape_end: ty.ClassVar[str] = "directed_association"


@element
class Generalization(Relationship):
    shape_end: ty.ClassVar[str] = "generalization"


@element
class Subsetting(Relationship):
    shape_end: ty.ClassVar[str] = "subsetting"


@element
class FeatureTyping(Relationship):
    shape_end: ty.ClassVar[str] = "feature_typing"


@element
class Redefinition(Relationship):
    shape_end: ty.ClassVar[str] = "redefinition"


RELATIONSHIP_TYPES = {
    "FeatureTyping": FeatureTyping,
    "OwnedBy": OwnedBy,
    "Redefinition": Redefinition,
    "Subsetting": Subsetting,
    "Superclassing": Generalization,
    # TODO: review and map the rest of the edge types
}

DEFAULT_RELATIONSHIP = DirectedAssociation


@element
class PartContainer(Partition):
    """A container for the parts diagram."""

    default_edge: ty.Type[Edge] = field(default=DirectedAssociation)

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
        " .subsetting > .round > ellipse": {
            "fill": "var(--jp-elk-node-stroke)",
        },
        " .feature_typing > .round > ellipse": {
            "fill": "var(--jp-elk-node-stroke)",
        },
        " .internal > .elknode": {
            "stroke": "transparent",
            "fill": "transparent",
        },
        # Necessary for having the viewport use the whole vertical height
        " .lm-Widget.jp-ElkView .sprotty > .sprotty-root > svg.sprotty-graph": {
            "height": "unset!important",
        }
    }


@ipyw.register
class SysML2ElkDiagram(ipyw.Box):
    """A SysML v2 Diagram"""

    compound: Compound = trt.Instance(Compound, args=())
    container: PartContainer = trt.Instance(PartContainer, args=())
    elk_app: ipyelk.Elk = trt.Instance(ipyelk.Elk)
    elk_layout: ipyelk.nx.XELKTypedLayout = trt.Instance(
        ipyelk.nx.XELKTypedLayout,
        kw=dict(selected_index=None),  # makes layout start collapsed
    )
    graph: nx.Graph = trt.Instance(nx.Graph, args=())
    id_mapper: Mapper = trt.Instance(Mapper, kw={})

    fit_btn: elk_tools.FitBtn = trt.Instance(elk_tools.FitBtn)
    toggle_btn: elk_tools.ToggleCollapsedBtn = trt.Instance(
        elk_tools.ToggleCollapsedBtn,
    )
    toolbar_buttons: list = trt.List(trait=trt.Instance(ipyw.Button))
    toolbar_accordion: ty.Dict[str, ipyw.Widget] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Instance(ipyw.Widget),
    )

    parts: ty.Dict[str, Part] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Instance(Part),
    )

    selected: ty.Tuple[str] = trt.Tuple()

    style: ty.Dict[str, dict] = trt.Dict(
        kw={
            " text.elklabel.node_type_label": {
                "font-style": "italic",
            },
            " parents": {
                "org.eclipse.elk.direction": "RIGHT",
                "org.eclipse.elk.nodeLabels.placement": "H_CENTER V_TOP INSIDE",
            },
        },
    )

    @trt.validate("children")
    def _validate_children(self, proposal):
        children = proposal.value
        if children:
            return children
        self._update_toolbar()
        return [self.elk_app]

    @trt.default("elk_app")
    def _make_app(self) -> ipyelk.Elk:
        elk_app = ipyelk.Elk(
            transformer=ipyelk.nx.XELK(
                source=(self.graph, None),
                label_key="labels",
                layouts=self.elk_layout.value,
            ),
            style=self.style,
            layout=dict(
                flex="1",
                height="100%",
                width="100%",
            ),
        )
        elk_app.observe(self._update_selected, "selected")
        return elk_app

    @trt.default("id_mapper")
    def _make_id_mapper(self) -> Mapper:
        transformer = self.elk_app.transformer
        relationships, hierarchy = transformer.source

        elk_to_items = transformer._elk_to_item or {}

        def id_from_item(item):
            id_ = None
            if isinstance(item, ipyelk.transform.Edge):
                id_ = item.data.get("properties", {}).get("@id")
            elif isinstance(getattr(item, "node", None), Compartment):
                id_ = next(hierarchy.predecessors(item)).node.id
            if id_ is None:
                self.log.debug(f"Could not parse: {item}")
            return id_

        from_elk_id = {
            elk_id: id_from_item(elk_item)
            for elk_id, elk_item in elk_to_items.items()
        }

        from_elk_id = {
            elk_id: sysml_id
            for elk_id, sysml_id in from_elk_id.items()
            if sysml_id is not None
        }
        return Mapper(from_elk_id)

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
        self.elk_app.toolbar.layout.width = "auto"
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

        container = PartContainer()
        parts = self._add_parts()

        for id_, part in parts.items():
            container.add_child(child=part, key=id_)
            # TODO: Look into adding children in a hierarchy, maybe make it configurable?
            # owner = self.parts.get((part.data.get("owner") or {}).get("@id"), container)
            # owner.add_child(child=part, key=id_)

        for (source, target, type_), edge in self.graph.edges.items():
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
            new_relationship = container.add_edge(
                source=parts[source],
                target=parts[target],
                cls=RELATIONSHIP_TYPES.get(type_, DEFAULT_RELATIONSHIP),
            )
            new_relationship.update(edge)

        container.defs = {**container.defs}
        self.container = container

    @trt.observe("container")
    def _update_app(self, *_):
        self.elk_app.transformer.source = self.compound(self.container)
        self.elk_app.style = self.container.style
        self.elk_app.diagram.defs = self.container.defs
        self.id_mapper = self._make_id_mapper()

    @trt.observe("selected")
    def _update_diagram_selections(self, *_):
        new_selections = self.id_mapper.get(*self.selected)
        diagram = self.elk_app.diagram
        if set(diagram.selected).symmetric_difference(new_selections):
            diagram.selected = new_selections

    def _update_selected(self, *_):
        new_selections = self.id_mapper.get(*self.elk_app.diagram.selected)
        if set(self.selected).symmetric_difference(new_selections):
            self.selected = new_selections

    @staticmethod
    def make_part(data: dict, width=220):
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
        part = Part(data=data, id=data["@id"], width=width)
        part.title = Compartment(headings=[
            f"""«{data["@type"]}»""",
            f"""{name}""",
        ])
        # TODO: add properties
        return part

    def _add_parts(self):
        old_parts = self.parts
        new_parts = {
            id_: self.make_part(node_data)
            for id_, node_data in self.graph.nodes.items()
            if node_data
            and id_ not in old_parts
        }
        old_parts.update(new_parts)
        return old_parts

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
                ),
            ],
        )

    def _update_diagram_layout_(self, *_):
        self.elk_app.transformer.layouts = self.elk_layout.value
        self.elk_app.refresh()
