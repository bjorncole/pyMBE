from functools import update_wrapper
import typing as ty

from warnings import warn

import ipywidgets as ipyw
import networkx as nx
import traitlets as trt

import ipyelk
from ipyelk.elements import layout_options as opt

from ...graph import SysML2LabeledPropertyGraph
from ..core import BaseWidget
from .parts import Part
from .part_diagram import PartDiagram
from .relationships import METATYPE_TO_RELATIONSHIP_TYPES, DirectedAssociation
from .tools import Toolbar, DEFAULT_BUTTON_KWARGS
from .utils import Mapper


@ipyw.register
class SysML2LPGWidget(ipyw.Box, BaseWidget):
    """An ipywidget to interact with a SysML2 model through an LPG."""

    description = trt.Unicode("Diagram").tag(sync=True)

    diagram: ipyelk.Diagram = trt.Instance(ipyelk.Diagram, args=())
    part_diagram: PartDiagram = trt.Instance(PartDiagram, args=())
    drawn_graph: nx.Graph = trt.Instance(nx.Graph, args=())

    id_mapper: Mapper = trt.Instance(Mapper, args=())
    parts: ty.Dict[str, Part] = trt.Dict(
        key_trait=trt.Unicode(),
        value_trait=trt.Instance(Part),
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

    # @trt.default("id_mapper")
    # def _make_id_mapper(self) -> Mapper:
    #     return Mapper(
    #         to_map={
    #             elk_id: getattr(element, "data", {}).get("@id")
    #             for elk_id, element in self.source.index.elements.items()
    #         },
    #     )

    # def _make_tools(self) -> ty.List[ipyelk.Tool]:
    #     view = self.diagram.view
    #     return [
    #         view.selection,
    #         view.fit_tool,
    #         view.center_tool,
    #         ipyelk.tools.PipelineProgressBar(),
    #     ]

    @trt.validate("children")
    def _validate_children(self, proposal: trt.Bunch):
        children = proposal.value
        if children:
            return children
        return [self.diagram]

    @trt.validate("diagram")
    def _validate_diagram(self, proposal: trt.Bunch):
        with self.log_out:
            print("started to update the darn diagram")
            diagram = proposal.value
            diagram.tools = diagram.tools[1:]

            toolbar = Toolbar(
                layout=dict(height="auto", width="auto", visibility="visible"),
                tools=self.diagram.tools,
            )
            toolbar.update_diagram = self._on_update_diagram_button_click

            toolbar.projection_selector.options = tuple(self.lpg.sysml_projections)
            # Configure buttons in the toolbar that update the diagram

            self.diagram.toolbar = toolbar

            trt.link((self.diagram, "tools"), (toolbar, "tools"))

            # FIXME: Remove the need to run these hacky "fixes"
            # toolbar._update_diagram_toolbar()
            print("finished updating the darn diagram!")
            return diagram

    @trt.default("layout")
    def _default_layout(self):
        return dict(
            height="100%",
            width="auto",
        )

    # TODO: Fix the selection, this may require to be brought back
    # @trt.observe("source")
    # def _update_mapper(self, *_):
    #     self.id_mapper = self._make_id_mapper()

    @trt.observe("sysml_projections")
    def _update_projection_selector(self, *_):
        self.toolbar.projection_selector.options = tuple(self.lpg.sysml_projections)

    @trt.observe("nodes_by_type")
    def _update_node_type_selector_options(self, *_):
        self.toolbar.update_dropdown_options(
            selector="nodes",
            options={
                f"{node_type} [{len(nodes)}]": nodes
                for node_type, nodes in sorted(self.lpg.nodes_by_type.items())
            },
        )

    @trt.observe("edges_by_type")
    def _update_edge_type_selector_options(self, *_):
        self.toolbar.update_dropdown_options(
            selector="edges",
            options={
                f"{edge_type} [{len(edges)}]": edges
                for edge_type, edges in sorted(self.lpg.edges_by_type.items())
                if edge_type in self.lpg.edge_types
            },
        )

    @trt.observe("selected")
    def _update_based_on_selection(self, *_):
        selected = self.selected
        self.toolbar.filter_to_path.disabled = (
            len(selected) != 2 or
            not all(isinstance(n, str) for n in selected)
        )
        self.toolbar.filter_by_dist.disabled = not selected

    @property
    def excluded_edge_types(self):
        included_edges = self.toolbar.edge_type_selector.value
        if not included_edges:
            return []

        return set(self.edge_types).difference((
                edges[0][2] for edges in included_edges
            ))

    @property
    def excluded_node_types(self):
        included_nodes = self.toolbar.node_type_selector.value
        if not included_nodes:
            return []

        return set(self.node_types).difference((
            self.lpg.graph.nodes[nodes[0]]["@type"]
            for nodes in included_nodes
        ))

    @property
    def selected_by_type_node_ids(self):
        return tuple(set(sum(
            map(
                list,
                self.toolbar.node_type_selector.value
            ), []
        )))

    @property
    def selected_by_type_nodes(self):
        return tuple(
            self.graph.nodes[id_]
            for id_ in sorted(self.selected_by_type_node_ids)
            if id_ in self.lpg.graph.nodes
        )

    @property
    def selected_by_type_edge_ids(self):
        return tuple(set(sum(
            map(
                list,
                self.toolbar.edge_type_selector.value
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
                failed = self._update_drawn_graph(button=button)
            except Exception as exc:
                self.log.warning(f"Button click for {button} failed: {exc}")
            finally:
                button.disabled = failed

    def _update_drawn_graph(self, button=None):
        failed = False
        toolbar = self.diagram.toolbar

        enforce_directionality = toolbar.enforce_directionality.value
        reversed_edges = toolbar.edge_type_reverser.value

        if reversed_edges and not enforce_directionality:
            raise ValueError(
                f"Reversing edge types: {reversed_edges} makes"
                "no sense since edges are not being enforced."
            )

        instructions: dict = self.get_projection_instructions(
            projection=toolbar.projection_selector.value,
        )
        new_graph = self.adapt(
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
                self.log.warning(
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
                self.log.warning(
                    "Could not find a spanning graph of distance "
                    f"{toolbar.max_distance.value} from these seeds: "
                    f"{self.selected}."
                )

        self.drawn_graph = new_graph

        # TODO: determine if we should refresh/fit/center the view

        return failed

    @trt.observe("part_diagram")
    def _update_diagram_view(self, *_):
        diagram = self.diagram
        part_diagram = self.part_diagram
        diagram.source = self.loader.load(part_diagram)
        diagram.style = part_diagram.style.copy()
        diagram.view.symbols = part_diagram.symbols

    @trt.observe("drawn_graph")
    def _update_part_diagram(self, change: trt.Bunch = None):
        if change and change.old not in (None, trt.Undefined):
            old = change.old
            del old
        graph = change.new

        part_diagram = PartDiagram()
        parts = self.parts
        new_parts = {
            id_: Part.from_data(node_data)
            for id_, node_data in graph.nodes.items()
            if node_data
               and id_ not in parts
        }
        parts.update(new_parts)

        for (source, target, metatype), edge_data in graph.edges.items():
            if source not in parts:
                self.log.warn(
                    f"Could not map source: {source} in "
                    f"'{metatype}' with {target}"
                )
                continue
            if target not in parts:
                self.log.warn(
                    f"Could not map target: {target} in "
                    f"'{metatype}' with {source}"
                )
                continue
            new_relationship = part_diagram.add_relationship(
                source=parts[source],
                target=parts[target],
                cls=METATYPE_TO_RELATIONSHIP_TYPES.get(
                    metatype,
                    DirectedAssociation,
                ),
                data=edge_data,
            )
        self.part_diagram = part_diagram

    @trt.observe("selected")
    def _update_diagram_selections(self, *_):
        new_selections = self._map_selections(*self.selected)
        view_selector = self.diagram.view.selection
        if set(view_selector.ids).symmetric_difference(new_selections):
            view_selector.ids = new_selections

    def _update_selected(self, *_):
        new_selections = self._map_selections(*self.diagram.view.selection.ids)
        if set(self.selected).symmetric_difference(new_selections):
            self.selected = new_selections

    def _map_selections(self, *selections: str) -> tuple:
        if not selections:
            return ()
        new_selections = self.id_mapper.get(*selections)
        if selections and not new_selections:
            self.id_mapper = self._make_id_mapper()
            new_selections = self.id_mapper.get(*selections)
        return tuple(new_selections)

    # TODO: Bring this back when the layout options are back in the toolbar
    # @trt.observe("elk_layout")
    # def _update_observers_for_layout(self, change: trt.Bunch):
    #     if change.old not in (None, trt.Undefined):
    #         change.old.unobserve(self._element_type_opt_change)
    #         del change.old
    #     change.new.observe(self._element_type_opt_change, "value")
