# a set of queries to run on Labeled Property Graphs

import networkx as NX
import math
from ..graph.filter_lib import banded_graph_filter
from ..client import SysML2Client
from .metamodel_navigator import *


def roll_up_lower_multiplicity(lpg: NX.MultiDiGraph, feat: dict, client: SysML2Client) -> int:

    bgf = banded_graph_filter()

    banded_featuring_graph = lpg.filter(
        edge_types=bgf['edge_types'],
        reverse_edge_types=bgf['reverse_edge_types']
    )

    banded_roots = [node
                    for node in banded_featuring_graph.nodes
                    if banded_featuring_graph.out_degree(node) == 0]

    corrected_mult = 1

    for part_tree_root in banded_roots:
        try:
            part_path = NX.shortest_path(
                banded_featuring_graph,
                feat['@id'],
                part_tree_root)
            # TODO: check that the path actually exists
            corrected_mult = math.prod(
                [feature_lower_multiplicity(client.elements_by_id[node], client)
                 for node in part_path])
        except NX.NetworkXNoPath:
            pass

    return corrected_mult


def roll_up_upper_multiplicity(lpg: NX.MultiDiGraph, feat: dict, client: SysML2Client) -> int:

    bgf = banded_graph_filter()

    banded_featuring_graph = lpg.filter(
        edge_types=bgf['edge_types'],
        reverse_edge_types=bgf['reverse_edge_types']
    )

    banded_roots = [node
                    for node in banded_featuring_graph.nodes
                    if banded_featuring_graph.out_degree(node) == 0]

    corrected_mult = 1

    for part_tree_root in banded_roots:
        try:
            part_path = NX.shortest_path(
                banded_featuring_graph,
                feat['@id'],
                part_tree_root)
            # TODO: check that the path actually exists
            corrected_mult = math.prod(
                [feature_upper_multiplicity(client.elements_by_id[node], client)
                 for node in part_path])
        except NX.NetworkXNoPath:
            pass

    return corrected_mult
