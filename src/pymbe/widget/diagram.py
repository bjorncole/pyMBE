import ipywidgets as ipyw
import networkx as nx
import traitlets as trt

import ipyelk
import ipyelk.nx

from ipyelk.contrib.shapes.connectors import Circle, Path, ConnectorDef, Point
from ipyelk.diagram.elk_model import ElkLabel


def make_circle_arrow_endpoint(r=6, closed=False):
    return ConnectorDef(
        children=[
            Circle(x=r*1/6, y=0, radius=r/5),
            Path.from_list([(r, -r/2), (r/2, 0), (r, r/2)], closed=closed),
        ],
        correction=Point(-1, 0),
        offset=Point(-r * 2 / 3, 0),
    )


def make_feature_typing_endpoint(r=6, closed=False):
    return ConnectorDef(
        children=[
            Circle(x=r*4/5, y=r/4, radius=r/20),
            Circle(x=r*4/5, y=-r/4, radius=r/20),
            Path.from_list([(r/2, -r/3), (0, 0), (r/2, r/3)], closed=closed),
        ],
        correction=Point(-1, 0),
        offset=Point(-r*2/3, 0),
    )


def make_redefinition_endpoint(r=6, closed=False):
    return ConnectorDef(
        children=[
            Path.from_list([(r*4/5, -r/3), (r*4/5, r/3)]),
            Path.from_list([(r/2, -r/3), (0, 0), (r/2, r/3)], closed=closed),
        ],
        correction=Point(-1, 0),
        offset=Point(-r*2/3, 0),
    )


class Diagram:
    """A SysML v2 Diagram"""

    _elk_diagram: ipyelk.Elk = trt.Instance(ipyelk.Elk)
    _display_box: ipyw.Box = trt.Instance(ipyw.VBox, args=())

    graph: nx.Graph = trt.Instance(nx.Graph, args=())
    layouts: ipyelk.nx.XELKTypedLayout() = trt.Instance(ipyelk.nx.XELKTypedLayout)

    def get_sub_graph(
        self,
        *,
        # add_ipyelk_data: bool = True,
        edges: (list, tuple) = None,
        edge_types: (list, tuple, str) = None,
    ):
        graph = self.graph
        subgraph = type(graph)()

        edges = edges or []

        edge_types = edge_types or []
        if isinstance(edge_types, str):
            edge_types = [edge_types]

        if edge_types:
            edges += [
                (source, target, data)
                for (source, target, type_), data in graph.edges.items()
                if type_ in edge_types
            ]

        if not edges:
            print(f"Could not find any edges of type: '{edge_types}'!")
            return subgraph

        nodes = {
            node_id: graph.nodes[node_id]
            for node_id in sum([  # sum(a_list, []) flattens a_list
                [source, target]
                for (source, target, data) in edges
            ], [])
        }

        for id_, node_data in nodes.items():
            node_data["id"] = id_
            type_label = [ElkLabel(
                id=f"""type_label_for_{id_}""",
                text=f"""«{node_data["@type"]}»""",
                properties={
                    "cssClasses": "node_type_label",
                },
            )] if "@type" in node_data else []
            node_data["labels"] = type_label + [node_data["name"]]

        subgraph.add_nodes_from(nodes.items())
        subgraph.add_edges_from(edges)

        return subgraph

    @trt.default("diagram")
    def _make_diagram(self) -> ipyw.HBox:
        layouts = self.layouts
        elk_diagram = ipyelk.Elk(
            transformer=ipyelk.nx.XELK(
                source=(self.graph, None),
                label_key="labels",
                layouts=layouts.value,
            ),
            style={
                " text.elklabel.node_type_label": {
                    "font-style": "italic",
                }
            },
        )

        def _element_type_opt_change(*_):
            self._elk_diagram.transformer.layouts = layouts.value
            self._elk_diagram.refresh()

        layouts.observe(_element_type_opt_change, "value")
        elk_diagram.layout.flex = "1"

        # Make the direction and label placement look better...
        self.set_layout_option(layouts, "Parents", "Direction", "UP")
        self.set_layout_option(layouts, "Label", "Node Label Placement", "H_CENTER V_TOP INSIDE")

        return ipyw.HBox([elk_diagram, layouts], layout=dict(height="60vh"))

    @trt.observe("layout")
    def _update_observers_for_layout(self, change: trt.Bunch):
        if change.old:
            raise NotImplementedError("Must unobserve!")
