from ..query.query import *
from ..query.metamodel_navigator import *
from .set_builders import *
from ..label import get_label_for_expression

# The playbooks here work to use set building steps to build up sets of instances from a given model

# Random builder for classifiers and features

# This playbook is an initial playbook that will randomly generate sequences to fill in sets that are interpretations
# of the user model


def random_generator_playbook(
    lpg: SysML2LabeledPropertyGraph,
    name_hints: dict,
) -> dict:

    can_interpret = validate_working_data(lpg)

    if not can_interpret:
        return {}

    all_elements = lpg.nodes

    # PHASE 1: Create a set of instances for part definitions based on usage multiplicities

    # work from part definitions

    ptg = lpg.get_projection("Part Typing Graph")
    scg = lpg.get_projection("Part Definition Graph")

    feature_sequences = build_sequence_templates(lpg=lpg)

    # will sub-divide abstract multiplicity
    abstracts = [
        node
        for node in ptg.nodes
        if all_elements[node].get("isAbstract")
    ]

    full_multiplicities = {}
    # look at all the types in the feature sequences
    for seq in feature_sequences:
        for feat in seq:
            for source, target in ptg.out_edges(feat):
                if "FeatureTyping" in ptg.get_edge_data(source, target):
                    feat_multiplicity = roll_up_upper_multiplicity(
                        lpg=lpg,
                        feature=all_elements[feat],
                    )
                    if target in abstracts:
                        specifics = list(scg.predecessors(target))
                        taken = 0
                        no_splits = len(specifics)
                        # need to sub-divide the abstract quantities
                        for index, specific in enumerate(specifics):
                            if index < (no_splits - 1):
                                draw = random.randint(0, feat_multiplicity)
                                taken = taken + draw
                            else:
                                draw = feat_multiplicity - taken
                            full_multiplicities.update({specific: draw})
                    else:
                        full_multiplicities.update({target: feat_multiplicity})

    instances_dict = {}

    for type_id, number in full_multiplicities.items():
        new_instances = create_set_with_new_instances(
            sequence_template=[all_elements[type_id]],
            quantities=[number],
            name_hints=name_hints,
        )

        instances_dict.update({type_id: new_instances})

    # PHASE 2: Combine sets of instances into sets that are marked as more general in the user model

    # "Roll up" the graph by looking at the successors to visited nodes that are unvisited, then forming a union
    # of the sets of the unvisited node's predecessors

    leaves = [node for node in scg.nodes if scg.in_degree(node) == 0]

    for leaf in leaves:
        if leaf not in instances_dict:
            new_instances = create_set_with_new_instances(
                sequence_template=[all_elements[leaf]],
                quantities=[1],
                name_hints=name_hints,
            )

            instances_dict.update({leaf: new_instances})

    visited_nodes = set(instances_dict.keys())
    unvisted_nodes = set(scg.nodes) - visited_nodes

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

    # Fill in any part definitions that don't have instances yet

    # TODO: Probably better done with real filter
    finishing_list = [
        node
        for node_id, node in all_elements.items()
        if node["@type"] == "PartDefinition"
        and node["@id"] not in instances_dict
    ]

    for element in finishing_list:
        new_instances = create_set_with_new_instances(
            sequence_template=[element],
            quantities=[1],
            name_hints=name_hints,
        )

        instances_dict.update({element["@id"]: new_instances})

    # PHASE 3: Expand the dictionaries out into feature sequences by pulling from instances developed here

    random_generator_playbook_phase_3(feature_sequences, all_elements, ptg, instances_dict)

    # PHASE 4: Expand sequences to support computations

    expr_sequences = build_expression_sequence_templates(lpg=lpg)

    # for indx, seq in enumerate(expr_sequences):
    #    print("Sequence number " + str(indx))
    #    for item in seq:
    #        print(get_label(all_elements[item], all_elements) + ", id = " + item)

    # Move through existing sequences and then start to pave further with new steps
    for expr_seq in expr_sequences:
        new_sequences = []
        for feature_id in expr_seq:
            # sample set will be the last element in the sequence for classifiers
            feature_data = all_elements[feature_id]
            if feature_id in instances_dict:
                new_sequences = instances_dict[feature_id]
            else:
                if "Expression" in feature_data["@type"] or "Literal" in feature_data["@type"]:
                    # Get the element type(s)
                    types: list = feature_data.get("type") or []
                    if isinstance(types, dict):
                        types = [types]
                    type_names = [
                        all_elements[type_["@id"]].get("name")
                        for type_ in types
                        if type_ and "@id" in type_
                    ]
                    type_names = [
                        str(type_name)
                        for type_name in type_names
                        if type_name
                    ]

                    new_sequences = extend_sequences_with_new_expr(
                        new_sequences,
                        get_label(feature_data, all_elements),
                        feature_data
                    )
                elif feature_data["@type"] == "Feature":
                    new_sequences = extend_sequences_with_new_value_holder(
                        new_sequences,
                        feature_data["name"],
                        feature_data
                    )
                else:
                    new_sequences = extend_sequences_by_sampling(
                        new_sequences,
                        1,
                        1,
                        [],
                        True,
                        feature_data,
                        all_elements
                    )
                instances_dict.update({feature_id: new_sequences})
    return instances_dict


def random_generator_playbook_phase_3(
    feature_sequences: list,
    all_elements: dict,
    ptg: nx.DiGraph,
    instances_dict: dict
) -> None:
    for feature_sequence in feature_sequences:
        new_sequences = []
        feat = None
        for index, feature_id in enumerate(feature_sequence):
            # sample set will be the last element in the sequence for classifiers
            feature = all_elements[feature_id]
            if feature["@type"] == "PartUsage":
                if feature_id in list(ptg.nodes):
                    types = list(ptg.successors(feature_id))
                else:
                    raise NotImplementedError("Cannot handle untyped features!")

                if len(types) > 1:
                    raise NotImplementedError("Cannot handle features with multiple types yet!")
                else:
                    typ = types[0]
            else:
                typ = feature_id

            if index == 0:
                new_sequences = instances_dict[typ]
            else:
                new_sequences = extend_sequences_by_sampling(
                    new_sequences,
                    feature_multiplicity(feature, all_elements, "lower"),
                    feature_multiplicity(feature, all_elements, "upper"),
                    [item for seq in instances_dict[typ] for item in seq],
                    False,
                    {},
                    {}
                )

            instances_dict.update({feature_id: new_sequences})


def build_sequence_templates(
    lpg: SysML2LabeledPropertyGraph
) -> list:
    part_featuring_graph = lpg.get_projection("Part Featuring Graph")
    sorted_feature_groups = []
    for comp in nx.connected_components(part_featuring_graph.to_undirected()):
        connected_sub = nx.subgraph(part_featuring_graph, list(comp))
        leaves = [node for node in connected_sub.nodes if connected_sub.in_degree(node) == 0]
        roots = [node for node in connected_sub.nodes if connected_sub.out_degree(node) == 0]
        for leaf in leaves:
            for root in roots:
                try:
                    leaf_path = nx.shortest_path(connected_sub, leaf, root)
                    sorted_feature_groups.append(leaf_path)
                except:
                    pass

        #sorted_feature_groups.append(
        #    [node for node in nx.topological_sort(connected_sub)]
        #)

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
    instances_in_process = tuple(instances_in_process)

    all_covered = all(
        next_instance in instances_in_process
        for next_instance in scg.predecessors(tested_node_id)
    )
    return all_covered


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


def build_expression_sequence_templates(lpg: SysML2LabeledPropertyGraph) -> list:
    all_elements = lpg.nodes
    evg = lpg.get_projection("Expression Value Graph")
    sorted_feature_groups = []
    for comp in nx.connected_components(evg.to_undirected()):
        connected_sub = nx.subgraph(evg, list(comp))
        leaves = [node for node in connected_sub.nodes if connected_sub.out_degree(node) == 0]
        roots = [node for node in connected_sub.nodes if connected_sub.in_degree(node) == 0]
        for leaf in leaves:
            for root in roots:
                try:
                    leaf_path = nx.shortest_path(connected_sub, root, leaf)
                    has_expression = any([
                        "Expression" in all_elements[step]["@type"]
                        or "Literal" in all_elements[step]["@type"]
                        or "AttributeUsage" == all_elements[step]["@type"]
                        for step in leaf_path
                    ])
                    if has_expression:
                        leaf_path.reverse()
                        sorted_feature_groups.append(leaf_path)
                except:
                    pass

        # sorted_feature_groups.append(
        #    [node for node in nx.topological_sort(connected_sub)]
        # )

    return sorted_feature_groups

def validate_working_data(
    lpg: SysML2LabeledPropertyGraph
) -> bool:
    """
    Helper method to check that the user model is valid for instance generation
    :return: A Boolean indicating that the user model is ready to be interpreted
    """

    # check that all the elements of the graph are in fact proper model elements

    all_non_relations = lpg.nodes
    for nr_key, nr in all_non_relations.items():
        try:
            nr_type = nr['@type']
        except KeyError:
            print("No type found in " + str(nr))
            return False
        except TypeError:
            print("Expecting dict of model element data, got string = " + nr)
        try:
            nr_id = nr["@id"]
        except KeyError:
            print("No type found in " + str(nr))
            return False

    return True