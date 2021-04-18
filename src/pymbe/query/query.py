# a set of queries to run on Labeled Property Graphs

import networkx as nx
import math
from ..graph.lpg import SysML2LabeledPropertyGraph
from .metamodel_navigator import *


def roll_up_lower_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feat: dict,
) -> int:
    return roll_up_multiplicity(
        lpg=lpg,
        feat=feat,
        feature_multiplicity_function=feature_lower_multiplicity,
    )


def roll_up_upper_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feat: dict,
) -> int:
    return roll_up_multiplicity(
        lpg=lpg,
        feat=feat,
        feature_multiplicity_function=feature_upper_multiplicity,
    )


def roll_up_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feat: dict,
    feature_multiplicity_function: callable,
) -> int:
    banded_featuring_graph = lpg.get_projection("expanded_banded_graph")
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
                source=feat['@id'],
                target=part_tree_root,
            )
            # TODO: check that the path actually exists
            corrected_mult = math.prod([
                feature_multiplicity_function(lpg.elements_by_id[node], lpg)
                for node in part_path
            ])
        except nx.NetworkXNoPath:
            pass
        except nx.NodeNotFound:
            # nothing to roll up, so just use own multiplicity
            corrected_mult = feature_multiplicity_function(feat, lpg)

    return corrected_mult
