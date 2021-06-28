from functools import update_wrapper
import typing as ty

from warnings import warn
from ipyelk.tools.tool import Tool

import ipywidgets as ipyw
import networkx as nx
import traitlets as trt

import ipyelk
from ipyelk.elements import layout_options as opt

from ...graph import SysML2LabeledPropertyGraph
from ..core import BaseWidget
from .parts import Part
from .part_diagram import PartDiagram
from .relationships import METATYPE_TO_RELATIONSHIP_TYPES, DirectedAssociation, Relationship
from .tools import Toolbar, DEFAULT_BUTTON_KWARGS
from .utils import Mapper


class Diagram(ipyelk.Diagram):
    """A slightly modified ipyelk Diagram to avoid issue with observer"""

    @trt.observe("tools")
    def _update_tools(self, change=None):
        # TODO: Submit PR with fix to ipyelk
        if change and change.old and change.old != trt.Undefined:
            for tool in change.old:
                tool.tee = None
                tool.on_done = None

        for tool in self.tools:
            tool.tee = self.pipe
            tool.on_done = self.refresh


@ipyw.register
class SysML2LPGWidget(ipyw.Box, BaseWidget):
    """An ipywidget to interact with a SysML2 model through an LPG."""

    description = trt.Unicode("Diagram").tag(sync=True)

    diagram: ipyelk.Diagram = trt.Instance(ipyelk.Diagram)
    part_diagram: PartDiagram = trt.Instance(PartDiagram, args=())
    drawn_graph: nx.Graph = trt.Instance(nx.Graph, args=())

    id_mapper: Mapper = trt.Instance(Mapper, args=())
    parts: ty.Dict[str, Part] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Instance(Part),
    )
    relationships: ty.Dict[str, Relationship] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Instance(Relationship),
    )

    lpg: SysML2LabeledPropertyGraph = trt.Instance(
        SysML2LabeledPropertyGraph,
        args=(),
    )

    loader: ipyelk.ElementLoader = trt.Instance(
        ipyelk.ElementLoader,
        kw=dict(
            default_node_opts={
                opt.Direction.identifier: opt.Direction(value="RIGHT").value,
                opt.HierarchyHandling.identifier: opt.HierarchyHandling().value,
            },
        ),
    )

    # TODO: Add functionality to link the selections
    selection_link: trt.link = trt.Instance(trt.link, allow_none=True)

    log_out = ipyw.Output()

    @trt.default("id_mapper")
    def _make_id_mapper(self) -> Mapper:
        elements = {
            **dict(self.diagram.source.index.elements.items()),
            **self.relationships,
        }
        return Mapper(
            to_map={
                elk_id: element.metadata.sysml_id
                for elk_id, element in elements.items()
                if hasattr(element.metadata, "sysml_id")
            },
        )

    @trt.validate("children")
    def _validate_children(self, proposal: trt.Bunch):
        children = proposal.value
        if children:
            return children
        return [self.diagram]

    def update(self, elements: dict):
        """Subclasses must implement this!"""
        self.lpg.update(elements)

        self.diagram.toolbar.update_dropdown_options(
            selector="nodes",
            options={
                f"{node_type} [{len(nodes)}]": nodes
                for node_type, nodes in sorted(self.lpg.nodes_by_type.items())
            },
        )

        self.diagram.toolbar.update_dropdown_options(
            selector="edges",
            options={
                f"{edge_type} [{len(edges)}]": edges
                for edge_type, edges in sorted(self.lpg.edges_by_type.items())
                if edge_type in self.lpg.edge_types
            },
        )

    @trt.default("diagram")
    def _make_diagram(self):
        # FIXME: This seems a bit more involved than it should be, check with Dane

        view = ipyelk.diagram.SprottyViewer(symbols=self.part_diagram.symbols)
        view.selection.observe(self._update_selected, "ids")

        tools = [
            view.selection,
            view.fit_tool,
            view.center_tool,
            ipyelk.tools.PipelineProgressBar(),
        ]

        toolbar = Toolbar(
            layout=dict(height="auto", width="auto", visibility="visible"),
            tools=tools,
            update_diagram = self._on_update_diagram_button_click,
        )
        trt.dlink(
            (self.lpg, "sysml_projections"),
            (toolbar.projection_selector, "options"),
            lambda x: tuple(x)
        )
        toolbar.projection_selector.options = tuple(self.lpg.sysml_projections)
        toolbar._update_children()
        toolbar.log_out = self.log_out

        # TODO: after ipyelk fix revert this back to ipyelk.Diagram
        diagram = Diagram(
            toolbar=toolbar,
            tools=tools,
            view=view,
        )
        trt.link((diagram, "tools"), (toolbar, "tools"))
        trt.link((diagram, "symbols"), (view, "symbols"))

        return diagram

    @trt.default("layout")
    def _default_layout(self):
        return dict(
            height="100%",
            width="auto",
        )

    @trt.observe("selected")
    def _update_based_on_selection(self, *_):
        selected = self.selected
        self.diagram.toolbar.filter_to_path.disabled = (
            len(selected) != 2 or
            not all(isinstance(node_id, str) for node_id in selected)
        )
        self.diagram.toolbar.filter_by_dist.disabled = not selected

    @property
    def excluded_edge_types(self):
        included_edges = self.diagram.toolbar.edge_type_selector.value
        if not included_edges:
            return []

        return set(self.lpg.edge_types).difference((
                edges[0][2] for edges in included_edges
            ))

    @property
    def excluded_node_types(self):
        included_nodes = self.diagram.toolbar.node_type_selector.value
        if not included_nodes:
            return []

        return set(self.lpg.node_types).difference((
            self.lpg.graph.nodes[nodes[0]]["@type"]
            for nodes in included_nodes
        ))

    @property
    def selected_by_type_node_ids(self):
        return tuple(set(sum(
            map(
                list,
                self.diagram.toolbar.node_type_selector.value
            ), []
        )))

    @property
    def selected_by_type_nodes(self):
        return tuple(
            self.lpg.graph.nodes[id_]
            for id_ in sorted(self.selected_by_type_node_ids)
            if id_ in self.lpg.graph.nodes
        )

    @property
    def selected_by_type_edge_ids(self):
        return tuple(set(sum(
            map(
                list,
                self.diagram.toolbar.edge_type_selector.value
            ), []
        )))

    @property
    def selected_by_type_edges(self):
        return tuple(
            self.lpg.graph.edges[id_]
            for id_ in sorted(self.selected_by_type_edge_ids)
            if id_ in self.lpg.graph.edges
        )

    def _on_update_diagram_button_click(self, button: ipyw.Button):
        with self.log_out:
            button.disabled = failed = True
            try:
                # print(f"Updating diagram with '{button.tooltip}' button.")
                failed = self._update_drawn_graph(button=button)
            except Exception as exc:
                warn(f"Button click for {button} failed: {exc}")
            finally:
                button.disabled = failed

    def _update_drawn_graph(self, button: ipyw.Button = None) -> bool:
        failed = False
        toolbar: Toolbar = self.diagram.toolbar

        enforce_directionality = toolbar.enforce_directionality.value
        reversed_edges = toolbar.edge_type_reverser.value

        if reversed_edges and not enforce_directionality:
            raise ValueError(
                f"Reversing edge types: {reversed_edges} makes"
                "no sense since edges are not being enforced."
            )

        instructions: dict = self.lpg.get_projection_instructions(
            projection=toolbar.projection_selector.value,
        )
        new_graph = self.lpg.adapt(
            excluded_edge_types={
                *instructions.get("excluded_edge_types", []),
                *self.excluded_edge_types,
            },
            excluded_node_types={
                *instructions.get("excluded_node_types", []),
                *self.excluded_node_types,
            },
            reversed_edge_types={
                *instructions.get("reversed_edge_types", []),
                *reversed_edges,
            },
        )

        if button is toolbar.filter_to_path:
            source, target = self.selected
            new_graph = self.lpg.get_path_graph(
                graph=new_graph,
                source=source,
                target=target,
                enforce_directionality=enforce_directionality,
            )
            if not new_graph:
                failed = True
                warn(
                    "Could not find path between " 
                    f"""{" and ".join(self.selected)}, with directionality """
                    "not" if not toolbar.enforce_directionality else ""
                    " enforced."
                )
        elif button is toolbar.filter_by_dist:
            new_graph = self.lpg.get_spanning_graph(
                graph=new_graph,
                seeds=self.selected,
                max_distance=toolbar.max_distance.value,
                enforce_directionality=enforce_directionality,
            )
            if not new_graph:
                failed = True
                warn(
                    "Could not find a spanning graph of distance "
                    f"{toolbar.max_distance.value} from these seeds: "
                    f"{self.selected}."
                )

        self.drawn_graph = new_graph

        return failed

    @trt.observe("part_diagram")
    def _update_diagram_view(self, change: trt.Bunch):
        diagram = self.diagram
        part_diagram = self.part_diagram
        diagram.style = part_diagram.style.copy()
        diagram.view.symbols = part_diagram.symbols
        diagram.source = self.loader.load(part_diagram)
        self.id_mapper = self._make_id_mapper()

    @trt.observe("drawn_graph")
    def _update_part_diagram(self, change: trt.Bunch = None):
        part_diagram = PartDiagram()

        if change is None:
            graph = self.drawn_graph
        else:
            if change.old not in (None, trt.Undefined):
                old = change.old
                del old
            if change.new:
                graph = change.new
            else:
                warn("Setting lpg.part_diagram to blank one")
                self.part_diagram = part_diagram
                return

        parts = self.parts
        new_parts = {
            node_id: Part.from_data(node_data)
            for node_id, node_data in graph.nodes.items()
            if node_data and node_id not in parts
        }
        parts.update(new_parts)

        self.relationships = {
            data["@id"]: part_diagram.add_relationship(
                source=parts[source],
                target=parts[target],
                cls=METATYPE_TO_RELATIONSHIP_TYPES.get(
                    metatype,
                    DirectedAssociation,
                ),
                data=data,
            )
            for (source, target, metatype), data in graph.edges.items()
            if source in parts and target in parts
        }
        self.part_diagram = part_diagram

    @trt.observe("selected")
    def _update_diagram_selections(self, *_):
        new_selections = self._map_selections(*self.selected)
        view_selector = self.diagram.view.selection
        if set(view_selector.ids).symmetric_difference(new_selections):
            view_selector.ids = new_selections

    def _update_selected(self, *_):
        new_selections = [
            id_
            for id_ in self._map_selections(*self.diagram.view.selection.ids)
            if id_ in self.elements_by_id
        ]
        if set(self.selected).symmetric_difference(new_selections):
            self.selected = new_selections

    def _map_selections(self, *selections: str) -> tuple:
        if not selections:
            return ()
        new_selections = self.id_mapper.get(*selections)
        if selections and not new_selections:
            self.id_mapper = self._make_id_mapper()
            new_selections = self.id_mapper.get(*selections)
        return new_selections

    # TODO: Bring this back when the layout options are back in the toolbar
    # @trt.observe("elk_layout")
    # def _update_observers_for_layout(self, change: trt.Bunch):
    #     if change.old not in (None, trt.Undefined):
    #         change.old.unobserve(self._element_type_opt_change)
    #         del change.old
    #     change.new.observe(self._element_type_opt_change, "value")
