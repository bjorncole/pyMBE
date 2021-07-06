# a set of queries to run on Labeled Property Graphs
import networkx as nx
import math

from ..graph.lpg import SysML2LabeledPropertyGraph
from ..interpretation.results import *
from .metamodel_navigator import *


def roll_up_lower_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feature: Element,
) -> int:
    return roll_up_multiplicity(
        lpg=lpg,
        feature=feature,
        bound="lower",
    )


def roll_up_upper_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feature: Element,
) -> int:
    return roll_up_multiplicity(
        lpg=lpg,
        feature=feature,
        bound="upper",
    )


def roll_up_multiplicity(
    lpg: SysML2LabeledPropertyGraph,
    feature: Element,
    bound: str,
) -> int:
    banded_featuring_graph = lpg.get_projection("Expanded Banded")

    # FIXME: Need projections to work correctly

    to_remove = []
    for edg in banded_featuring_graph.edges:
        if edg[2] == 'ImpliedParameterFeedforward':
            to_remove.append(edg)

    for remover in to_remove:
        banded_featuring_graph.remove_edge(remover[0], remover[1])

    banded_roots = [
        node
        for node in banded_featuring_graph.nodes
        if banded_featuring_graph.out_degree(node) < 1
    ]

    model = lpg.model
    total_mult = 0
    feature_id = feature._id
    for part_tree_root in banded_roots:
        # case where the usage is actually top of a nesting set
        if feature_id == part_tree_root:
            total_mult = 1
        try:
            part_paths = nx.all_simple_paths(
                banded_featuring_graph,
                source=feature_id,
                target=part_tree_root,
            )
            for part_path in part_paths:
                # TODO: check that the path actually exists
                corrected_mult = math.prod([
                    feature_multiplicity(model.elements[element_id], bound)
                    for element_id in part_path
                ])
                total_mult += corrected_mult
        except nx.NetworkXNoPath:
            print("Found no path when rolling up multiplicity.")
            pass
        except nx.NodeNotFound:
            # nothing to roll up, so just use own multiplicity
            total_mult = feature_multiplicity(feature, bound)

    return total_mult


def roll_up_multiplicity_for_type(
    lpg: SysML2LabeledPropertyGraph,
    typ: dict,
    bound: str,
) -> int:

    rdg = lpg.get_projection("Redefinition and Subsetting")
    cug = lpg.get_projection("Connection")
    # FIXME: Need projections to work correctly

    to_remove = []

    for edg in rdg.edges:
        if edg[2] == 'ImpliedParameterFeedforward':
            to_remove.append(edg)

    for remover in to_remove:
        rdg.remove_edge(remover[0], remover[1])

    running_total = 0
    ptg = lpg.get_projection("Part Typing")

    all_elements = lpg.model.elements
    if typ['@id'] in ptg.nodes:
        feat_ids = get_features_typed_by_type(lpg, typ['@id'])
        #feat_ids = ptg.predecessors(typ['@id'])
        for feat_id in feat_ids:
            running_total += roll_up_multiplicity(
                lpg,
                all_elements[feat_id],
                bound,
            )
            if feat_id in rdg and feat_id not in cug:
                redef_ids = rdg.predecessors(feat_id)
                for redef_id in redef_ids:
                    running_total += roll_up_multiplicity(
                        lpg,
                        all_elements[redef_id],
                        bound,
                )
        return running_total
    else:
        return 0


def get_types_for_feature(
    lpg: SysML2LabeledPropertyGraph,
    feature_id: str,
) -> List[str]:

    ptg = lpg.get_projection("Part Typing")
    rdg = lpg.get_projection("Redefinition and Subsetting")

    # approach is to see source and target ends of feature typing and then see if there is a redefinition
    # path back to the requested feature

    types = []
    if feature_id in list(ptg.nodes):
        types = list(ptg.successors(feature_id))
    elif feature_id in list(rdg.nodes):
        feature_neighbors = list(nx.dfs_preorder_nodes(rdg, feature_id))
        for neighbor in feature_neighbors:
            # if the redefinitions along the way point to types, include those types
            if neighbor in list(ptg.nodes):
                types += list(ptg.successors(neighbor))

    return types


def get_features_typed_by_type(
    lpg: SysML2LabeledPropertyGraph,
    type_id: str,
) -> list:

    ptg = lpg.get_projection("Part Typing")
    rdg = lpg.get_projection("Redefinition and Subsetting")

    # approach is to look at clusters of redefinitions and see if the most redefined connects to the type

    features = []

    if type_id in list(ptg.nodes):
        features = list(ptg.predecessors(type_id))
    elif type_id in list(rdg.nodes):
        for comp in nx.connected_components(rdg.to_undirected()):
            connected_sub = nx.subgraph(rdg, list(comp))
            roots = [node for node in connected_sub.nodes if connected_sub.out_degree(node) == 0]
            for root in roots:
                if root in list(ptg.nodes):
                    for item in list(comp):
                        if item not in features:
                            features += item

    return features


def build_element_owner_sequence(
        element: dict,
        all_elements: list,
        seq: list = [],
) -> list:
    if "owner" not in element or element["owner"] is None:
        return seq

    seq.append(element)

    return build_element_owner_sequence(
        all_elements[element["owner"]["@id"]],
        all_elements,
        seq,
    )


def calculate_signature(element: dict, all_elements: dict) -> str:
    owned_sequence = build_element_owner_sequence(
        element,
        all_elements,
        [],
    )

    sig_seq = []
    for item in owned_sequence:
        if "name" in item and item["name"] != "":
            sig_seq.append(item["name"])
        else:
            sig_seq.append(get_label(item))

    sig_seq.reverse()

    return "::".join(sig_seq)
