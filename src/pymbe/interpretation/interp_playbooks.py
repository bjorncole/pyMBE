from .set_builders import create_set_with_new_instances
import networkx as nx
import random
from ..query.query import *

# The playbooks here work to use set building steps to build up sets of instances from a given model

# Random builder for classifiers and features

# This playbook is an initial playbook that will randomly generate sequences to fill in sets that are interpretations
# of the user model

def random_generator_playbook(
    lpg: SysML2LabeledPropertyGraph,
    all_elements: dict,
    name_hints: dict
) -> dict:

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

    print(full_multiplicities)

    instances_dict = {}

    for type_id, number in full_multiplicities.items():
        new_instances = create_set_with_new_instances(
            sequence_template=[all_elements[type_id]],
            quantities=[number],
            name_hints=name_hints
        )

        instances_dict.update({type_id: new_instances})

    # PHASE 2: Combine sets of instances into sets that are marked as more general in the user model



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

def check_subset_coverage_in_graph(
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

def push_classifiers_more_general(self):
    """
    Take specific classifiers and push the calculated instances to more general classifiers
    :return:
    """
    white_list = []

    for classifier_instance_dict in self.classifier_instance_dicts:
        # TODO: Use sets and set differencing to remove visited nodes
        white_list = list(self.session.graph_manager.superclassing_graph.nodes())
        black_list = list(classifier_instance_dict.keys())
        for black in black_list:
            white_list.remove(black)
        root_drop = []
        for white in white_list:
            # try to pull out items with no incoming links
            if self.session.graph_manager.superclassing_graph.in_degree(white) == 0:
                classifier_instance_dict.update({white: []})
                root_drop.append(white)
        for rd in root_drop:
            black_list.append(rd)
            white_list.remove(rd)

        first_pass_dict = {}

        # try to cover all white list nodes with inputs from black-listed nodes, first pass is pulling data
        # from classifier_instance_dict as is

        for key in classifier_instance_dict:
            for gen in self.session.graph_manager.superclassing_graph.successors(key):
                # bail if we've already been here
                if gen in black_list:
                    break
                gen_covered = check_subset_coverage_in_graph()
                if gen_covered:
                    #if the current node is white and all predecessors are black, then can roll instances up
                    first_pass_dict.update({gen: instance_working_list})
                    white_list.remove(gen)
                    black_list.append(gen)

        classifier_instance_dict.update(first_pass_dict)

    return len(white_list)