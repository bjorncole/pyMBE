from .set_builders import create_set_with_new_instances
from .set_builders import extend_sequences_by_sampling
import networkx as nx
import random
from ..query.query import *
from ..label import get_label

# The playbooks here work to use set building steps to build up sets of instances from a given model

# Random builder for classifiers and features

# This playbook is an initial playbook that will randomly generate sequences to fill in sets that are interpretations
# of the user model

def random_generator_playbook(
    lpg: SysML2LabeledPropertyGraph,
    name_hints: dict
) -> dict:

    all_elements = lpg.nodes

    # PHASE 1: Create a set of instances for part definitions based on usage multiplicities

    # work from part definitions

    ptg = lpg.get_projection("Part Typing Graph")
    scg = lpg.get_projection("Part Definition Graph")

    feature_sequences = build_sequence_templates(lpg=lpg)

    # will sub-divide abstract multiplicity
    abstracts = [node for node in ptg.nodes if all_elements[node]['isAbstract']]

    full_multiplicities = {}

    # look at all the types in the feature sequences
    for seq in feature_sequences:
        for feat in seq:
            for edg in ptg.out_edges(feat):
                if 'FeatureTyping' in list(ptg.get_edge_data(edg[0], edg[1]).keys()):
                    feat_multiplicity = roll_up_upper_multiplicity(lpg, all_elements[feat])
                    if (edg[1] in abstracts):
                        specifics = list(scg.predecessors(edg[1]))
                        taken = 0
                        no_splits = len(specifics)
                        # need to sub-divide the abstract quantities
                        for indx, specific in enumerate(specifics):
                            if indx < no_splits - 1:
                                draw = random.randint(0, feat_multiplicity)
                                taken = taken + draw
                            else:
                                draw = feat_multiplicity - taken
                            full_multiplicities.update({specific: draw})
                    else:
                        full_multiplicities.update({edg[1]: feat_multiplicity})

    instances_dict = {}

    for type_id, number in full_multiplicities.items():
        new_instances = create_set_with_new_instances(
            sequence_template=[all_elements[type_id]],
            quantities=[number],
            name_hints=name_hints
        )

        instances_dict.update({type_id: new_instances})

    # PHASE 2: Combine sets of instances into sets that are marked as more general in the user model

    # Find nodes in the part definition graph that aren't already in the instances dict but have no subsets

    leaves = [node for node in scg.nodes if scg.in_degree(node) == 0]

    for leaf in leaves:
        if leaf not in instances_dict:
            new_instances = create_set_with_new_instances(
                sequence_template=[all_elements[leaf]],
                quantities=[1],
                name_hints=name_hints
            )

            instances_dict.update({leaf: new_instances})

    visited_nodes = set(instances_dict.keys())
    unvisted_nodes = set(scg.nodes) - visited_nodes

    # "Roll up" the graph by looking at the successors to visited nodes that are unvisited, then forming a union
    # of the sets of the unvisited node's predecessors

    safety = 0

    while len(unvisted_nodes) > 0 and safety < 100:

        node_visits = []

        for key in visited_nodes:
            for gen in scg.successors(key):
                # bail if we've already been here
                if gen in visited_nodes:
                    break
                if is_node_covered_by_subsets(lpg, gen, instances_dict) and gen not in node_visits:
                    update_dict = generate_superset_instances(scg, gen, visited_nodes, instances_dict)
                    instances_dict.update(update_dict)
                    if len(update_dict.keys()) > 0:
                        node_visits.append(gen)

        for touched_node in node_visits:
            visited_nodes.add(touched_node)
            unvisted_nodes.remove(touched_node)

        safety = safety + 1

    # PHASE 3: Expand the dictionaries out into feature sequences by pulling from instances developed here

    for feat_seq in feature_sequences:
        working_sequences = []
        for indx, feat in enumerate(feat_seq):
            print(get_label(all_elements[feat], all_elements) + ', id ' + feat)
            # sample set will be the last element in the sequence for classifiers

            if indx == 0:
                first_sequences = extend_sequences_by_sampling(
                    [],
                    1,
                    1,
                    instances_dict[feat]
                )
                working_sequences.append(first_sequences)
            else:
                # get the type
                pass

    return instances_dict

def build_sequence_templates(
    lpg: SysML2LabeledPropertyGraph
) -> list:
    part_featuring_graph = lpg.get_projection("Part Featuring Graph")
    sorted_feature_groups = []
    for comp in nx.connected_components(part_featuring_graph.to_undirected()):
        connected_sub = nx.subgraph(part_featuring_graph, list(comp))
        sorted_feature_groups.append(
            [node for node in nx.topological_sort(connected_sub)]
        )

    return sorted_feature_groups

def is_node_covered_by_subsets(
    lpg: SysML2LabeledPropertyGraph,
    tested_node_id: str,
    instances_in_process: dict
) -> bool:
    """
    Check that the specializing types (subsets in instance sets) of a given node have fully defined instance sets
    :param lpg: Working label property graph
    :param tested_node_id: node to check
    :param instances_in_process: instance list produced so far
    :return: verdict on coverage
    """

    scg = lpg.get_projection("Part Definition Graph")

    next_level = scg.predecessors(tested_node_id)

    covered = True

    for next in next_level:
        if next not in list(instances_in_process.keys()):
            covered = False

    return covered

# FIXME: Fix to match new steps

def generate_superset_instances(
        part_def_graph: nx.MultiDiGraph,
        superset_node: str,
        visited_nodes: set,
        instances_dict: dict
) -> dict:
    """
    Take specific classifiers and push the calculated instances to more general classifiers
    :return:
    """

    new_superset = []
    subset_nodes = part_def_graph.predecessors(superset_node)
    if all(subset_node in visited_nodes for subset_node in subset_nodes):
        for subset_node in part_def_graph.predecessors(superset_node):
            new_superset.extend(instances_dict[subset_node])
    else:
        return {}

    return {superset_node: new_superset}