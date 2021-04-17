# a set of queries to run on Labeled Property Graphs

import math

import networkx as nx

from ..graph.lpg import SysML2LabeledPropertyGraph
from .metamodel_navigator import *


def roll_up_lower_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feat: dict,
) -> int:

    banded_featuring_graph = lpg.adapt("banded_graph")

    banded_roots = [
        node
        for node in banded_featuring_graph.nodes
        if banded_featuring_graph.out_degree(node) < 1
    ]

    corrected_mult = 1

    for part_tree_root in banded_roots:
        try:
            part_path = nx.shortest_path(
                banded_featuring_graph,
                feat['@id'],
                part_tree_root)
            # TODO: check that the path actually exists
            corrected_mult = math.prod([
                feature_lower_multiplicity(lpg.elements_by_id[node], lpg)
                for node in part_path
            ])
        except nx.NetworkXNoPath:
            pass

    return corrected_mult


def roll_up_upper_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feat: dict,
) -> int:

    banded_featuring_graph = lpg.adapt("banded_graph")

    banded_roots = [
        node
        for node in banded_featuring_graph.nodes
        if banded_featuring_graph.out_degree(node) == 0
    ]

    corrected_mult = 1

    for part_tree_root in banded_roots:
        try:
            part_path = nx.shortest_path(
                banded_featuring_graph,
                feat['@id'],
                part_tree_root)
            # TODO: check that the path actually exists
            corrected_mult = math.prod([
                feature_upper_multiplicity(lpg.elements_by_id[node], lpg)
                for node in part_path
            ])
        except nx.NetworkXNoPath:
            pass

    return corrected_mult
