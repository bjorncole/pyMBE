import typing as ty

import ipywidgets as ipyw
import traitlets as trt
from ipyelk import Diagram, ElementLoader
from ipyelk.elements import Label, Node, Port

from ...interpretation.interpretation import repack_instance_dictionaries
from ...model import Model
from .part_diagram import PartDiagram

NODE_LAYOUT_OPTIONS = {
    "org.eclipse.elk.portLabels.placement": "INSIDE",
    "org.eclipse.elk.nodeSize.constraints": "NODE_LABELS PORTS PORT_LABELS MINIMUM_SIZE",
    "org.eclipse.elk.nodeLabels.placement": "H_CENTER V_CENTER",
}


class InterpretationDiagram(ipyw.VBox):

    diagram: Diagram = trt.Instance(Diagram, kw=dict(layout=dict(height="100%")))
    m0_interpretation: ty.Dict = trt.Dict()
    model: Model = trt.Instance(Model)
    port_size: int = trt.Integer(15)

    @trt.validate("children")
    def _validate_children(self, proposal: trt.Bunch):
        children = proposal.value
        if children:
            return children
        return [self.diagram]

    @trt.validate("layout")
    def _validate_layout(self, proposal: trt.Bunch):
        layout = proposal.value or {}
        layout["height"] = "100%"
        return layout

    @trt.observe("m0_interpretation")
    def _update_for_new_interpretation(self, change: trt.Bunch):
        part_diagram = PartDiagram()

        repacked = repack_instance_dictionaries(self.m0_interpretation, self.model)

        def is_draw_kind(entry, kind):
            draw_kind = next(iter(entry.value)).owning_entry.draw_kind
            return draw_kind and kind in draw_kind

        def get_parent_node(instance):
            metatype = instance.element._metatype
            elk_node = elk_nodes.get(metatype)
            if not elk_node:
                elk_nodes[metatype] = elk_node = Node(
                    labels=[Label(text=f"{metatype}s")],
                    layoutOptions=NODE_LAYOUT_OPTIONS,
                )
                part_diagram.add_child(elk_node)
            return elk_node

        nodes = [entry.value for entry in repacked if is_draw_kind(entry, "Rectangle")]
        elk_nodes = {}
        for interpreted_nodes in nodes:
            for sequence in interpreted_nodes:
                parent_node = None
                for instance in sequence.instances:
                    if instance not in elk_nodes:
                        if parent_node is None:
                            parent_node = get_parent_node(instance)
                        elk_nodes[instance] = elk_node = parent_node.add_child(
                            Node(
                                labels=[Label(text=instance.name)],
                                layoutOptions=NODE_LAYOUT_OPTIONS,
                            ),
                        )
                    parent_node = elk_node

        ports = [entry.value for entry in repacked if is_draw_kind(entry, "Port")]
        elk_ports = {}
        for port_set in ports:
            for sequence in port_set:
                *_, node, port = sequence.instances
                elk_ports[port] = elk_nodes[node].add_port(
                    port=Port(
                        layoutOptions={
                            "org.eclipse.elk.port.borderOffset": f"-{self.port_size}",
                        },
                        labels=[Label(text=port.name.split("#")[-1])],
                        width=self.port_size,
                        height=self.port_size,
                    ),
                )

        lines = [entry.value for entry in repacked if is_draw_kind(entry, "Line")]
        for line in lines:
            for connection in line:
                src, tgt = connection.get_line_ends()
                part_diagram.add_edge(
                    source=elk_ports[src.instances[-1]],
                    target=elk_ports[tgt.instances[-1]],
                )
        loader = ElementLoader()
        diagram = self.diagram
        diagram.source = loader.load(part_diagram)
        diagram.style = part_diagram.style
        diagram.view.symbols = part_diagram.symbols
