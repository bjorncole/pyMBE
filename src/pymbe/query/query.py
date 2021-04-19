# a set of queries to run on Labeled Property Graphs
import networkx as nx
import math
from ..graph.lpg import SysML2LabeledPropertyGraph
from .metamodel_navigator import *


def roll_up_lower_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feature: dict,
) -> int:
    return roll_up_multiplicity(
        lpg=lpg,
        feature=feature,
        bound="lower",
    )


def roll_up_upper_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feature: dict,
) -> int:
    return roll_up_multiplicity(
        lpg=lpg,
        feature=feature,
        bound="upper",
    )


def roll_up_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feature: dict,
    bound: str,
) -> int:
    banded_featuring_graph = lpg.get_projection("Expanded Banded Graph")
    banded_roots = [
        node
        for node in banded_featuring_graph.nodes
        if banded_featuring_graph.out_degree(node) < 1
    ]

    all_elements = lpg.elements_by_id

    corrected_mult = 1
    for part_tree_root in banded_roots:
        try:
            part_path = nx.shortest_path(
                banded_featuring_graph,
                source=feature['@id'],
                target=part_tree_root,
            )
            # TODO: check that the path actually exists
            corrected_mult = math.prod([
                feature_multiplicity(all_elements[node], all_elements, bound)
                for node in part_path
            ])
        except nx.NetworkXNoPath:
            pass
        except nx.NodeNotFound:
            # nothing to roll up, so just use own multiplicity
            corrected_mult = feature_multiplicity(feature, all_elements, bound)

    return corrected_mult
