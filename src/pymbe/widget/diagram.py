from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import ipywidgets as ipyw
import networkx as nx
import traitlets as trt
import typing as ty

import ipyelk
from ipyelk.contrib.library.block import (
    Aggregation,
    Block,
    BlockDiagram,
    Composition,
)
from ipyelk.contrib.molds import connectors as conn, structures
from ipyelk.diagram import Exporter
import ipyelk.tools
from ipyelk.elements import (
    Compartment,
    Edge,
    Label,
    Mark,
    MarkFactory,
    Node,
    Port,
    Record,
    layout_options as opt,
    shapes,
)

# class CenterButton(elk_tools.ToolButton):
#
#     def handler(self, *_):
#         diagram = self.app.diagram
#         diagram.center(retain_zoom=True)
#
#
# class FitButton(elk_tools.ToolButton):
#
#     def handler(self, *_):
#         diagram = self.app.diagram
#         diagram.fit(padding=50)


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

    fit: FitButton = trt.Instance(FitButton)
    center: CenterButton = trt.Instance(CenterButton)
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
    style: ty.Dict[str, dict] = trt.Dict(kw={})

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
                if item in hierarchy:
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

    @trt.default("center")
    def _make_center_button(self) -> CenterButton:
        return CenterButton(
            app=self.elk_app,
            description="",
            icon="compress",
            layout=dict(height="40px", width="40px"),
            tooltip="Center Diagram",
        )

    @trt.default("fit")
    def _make_fit_button(self) -> FitButton:
        return FitButton(
            app=self.elk_app,
            description="",
            icon="expand-arrows-alt",
            layout=dict(height="40px", width="40px"),
            tooltip="Fit Diagram",
        )

    @trt.default("toolbar_buttons")
    def _make_toolbar_buttons(self):
        return [self.fit, self.center]

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

    @trt.observe("container")
    def _update_app(self, *_):
        self.elk_app.transformer.source = self.compound(self.container)
        self.elk_app.style = self.container.style
        self.elk_app.diagram.defs = self.container.defs
        self.id_mapper = self._make_id_mapper()

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
