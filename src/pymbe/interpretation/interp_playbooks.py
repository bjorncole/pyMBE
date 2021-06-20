from random import randint
from uuid import uuid4

import networkx as nx

from ..graph.lpg import SysML2LabeledPropertyGraph
from ..label import get_label, get_label_for_id
from ..query.metamodel_navigator import map_inputs_to_results
from ..query.query import (
    feature_multiplicity,
    get_types_for_feature,
    roll_up_multiplicity_for_type,
    safe_get_featuring_type_by_id,
)
from .set_builders import (
    create_set_with_new_instances,
    extend_sequences_by_sampling,
    extend_sequences_with_new_expr,
    extend_sequences_with_new_value_holder,
)

# The playbooks here work to use set building steps to build up sets of instances from a given model

# Random builder for classifiers and features

# This playbook is an initial playbook that will randomly generate sequences to fill in sets that are interpretations
# of the user model

TYPES_FOR_FEATURING = (
    "AttributeUsage",
    "ConnectionUsage",
    "InterfaceUsage",
    "PartUsage",
    "PortUsage",
)

TYPES_FOR_ROLL_UP_MULTIPLICITY = (
    "AttributeDefinition",
    "ConnectionDefinition",
    "DataType",
    "InterfaceDefinition",
    "PartDefinition",
    "PortDefinition",
)


def random_generator_playbook(
    lpg: SysML2LabeledPropertyGraph,
    name_hints: dict,
) -> dict:

    can_interpret = validate_working_data(lpg)

    if not can_interpret:
        return {}

    all_elements = lpg.nodes

    # PHASE 0: Add implicit relationships between parameters to assure equation solving

    random_generator_phase_0_interpreting_edges(lpg)

    # PHASE 1: Create a set of instances for part definitions based on usage multiplicities

    # work from part definitions to establish how many definitions are needed

    ptg = lpg.get_projection("Part Typing Graph")
    scg = lpg.get_projection("Part Definition Graph")

    feature_sequences = build_sequence_templates(lpg=lpg)

    full_multiplicities = random_generator_phase_1_multiplicities(lpg, ptg, scg)

    instances_dict = {}

    for type_id, number in full_multiplicities.items():
        new_instances = create_set_with_new_instances(
            sequence_template=[all_elements[type_id]],
            quantities=[number],
            name_hints=name_hints,
        )

        instances_dict.update({type_id: new_instances})

    # pick up the definitions that aren't matched to a usage yet

    random_generator_playbook_phase_1_singletons(lpg, scg, instances_dict)

    # PHASE 2: Combine sets of instances into sets that are marked as more general in the user model

    # "Roll up" the graph through a breadth-first search from the most general classifier down to the most specific
    # and then move in reverse order from the specific (subset) to the general (superset)

    random_generator_playbook_phase_2_rollup(scg, instances_dict)

    # Fill in any part definitions that still don't have instances yet (because they get filtered out by the
    # Part Definition pre-defined graph (neither typed nor subclassed))

    random_generator_playbook_phase_2_unconnected(all_elements, instances_dict)

    # PHASE 3: Expand the dictionaries out into feature sequences by pulling from instances developed here

    random_generator_playbook_phase_3(feature_sequences, all_elements, lpg, instances_dict)

    # PHASE 4: Expand sequences to support computations

    expr_sequences = build_expression_sequence_templates(lpg=lpg)

    # for indx, seq in enumerate(expr_sequences):
    #    print("Sequence number " + str(indx))
    #    for item in seq:
    #        print(get_label(all_elements[item], all_elements) + ", id = " + item)

    # Move through existing sequences and then start to pave further with new steps

    random_generator_playbook_phase_4(expr_sequences, lpg, instances_dict)

    # attached connector ends to sequences(

    random_generator_playbook_phase_5(lpg, lpg.get_projection("Connection Graph"), instances_dict)

    return instances_dict


def random_generator_phase_0_interpreting_edges(lpg: SysML2LabeledPropertyGraph):
    """
    Pre-work for the interpretation to support expression evaluations
    :param client: Active SysML Client
    :param lpg: Working Labeled Property Graph
    :return: None - side effect is update to LPG with new edges
    """
    new_edges = [
        (source, target, metatype, {
            "@id": f"_{uuid4()}",
            "@type": metatype,
            "label": metatype,
            "relatedElement": [
                {"@id": source},
                {"@id": target},
            ],
            "source": [{"@id": source}],
            "target": [{"@id": target}],
        })
        for source, target, metatype in map_inputs_to_results(lpg)
    ]
    new_elements = {
        data["@id"]: data
        for *_, data in new_edges
    }

    lpg.elements_by_id = {**lpg.elements_by_id, **new_elements}
    for edge in new_edges:
        new_edg = {(edge[0:3]): edge[3]}
        lpg.edges.update(new_edg)

    lpg.graph.add_edges_from([
            [
                edge[0],  # source node (str id)
                edge[1],  # target node (str id)
                edge[2],  # edge metatypetype (str name)
                edge[3],  # edge data (dict)
            ]
            for edge in new_edges
        ])


def random_generator_phase_1_multiplicities(
    lpg: SysML2LabeledPropertyGraph,
    ptg: nx.DiGraph,
    scg: nx.DiGraph,
) -> dict:
    """
    Calculates the multiplicities for classifiers in the considered model to support initial generation
    :param lpg: Active SysML graph
    :param ptg: Part Typing Graph projection from the LPG
    :param scg: Subclassing Graph projection from the LPG
    :return: dictionary of multiplicities for instance generation, indexed by classifier ID
    """


    abstracts = [
        node
        for node in ptg.nodes
        if lpg.nodes[node].get("isAbstract")
    ]

    # find the maximal amount of types directly based on instances
    type_multiplicities = {
        pt: roll_up_multiplicity_for_type(
            lpg,
            lpg.nodes[pt],
            "upper",
        )
        for pt in ptg.nodes
        if lpg.nodes[pt]["@type"] in TYPES_FOR_ROLL_UP_MULTIPLICITY
    }

    full_multiplicities = {}
    # look at all the types in the feature sequences
    for typ, mult in type_multiplicities.items():
        if typ in abstracts:
            specifics = list(scg.successors(typ))
            taken = 0
            no_splits = len(specifics)
            # need to sub-divide the abstract quantities
            for index, specific in enumerate(specifics):
                if index < (no_splits - 1):
                    draw = randint(0, mult)
                    taken = taken + draw
                else:
                    draw = mult - taken
                full_multiplicities[specific] = draw
        else:
            full_multiplicities[typ] = mult

    return full_multiplicities


def random_generator_playbook_phase_1_singletons(
    lpg: SysML2LabeledPropertyGraph,
    scg: nx.DiGraph,
    instances_dict: dict,
) -> None:
    """
    Calculates instances for classifiers that aren't directly typed (but may have members or be superclasses for
    model elements that have sequences generated for them)
    :param lpg: Active SysML graph
    :param scg: Subclassing Graph projection from the LPG
    :param instances_dict: Working dictionary of interpreted sequences for the model
    :return: None - side effect is addition of new instances to the instances dictionary
    """

    all_elements = lpg.nodes

    # need to generate single instances at leaves that don't match types
    leaves = [node for node in scg.nodes if scg.out_degree(node) == 0]

    new_instances = {
        leaf: create_set_with_new_instances(
            sequence_template=[all_elements[leaf]],
            quantities=[1],
            name_hints={},
        )
        for leaf in leaves
        if leaf not in instances_dict
    }
    instances_dict.update(new_instances)


def random_generator_playbook_phase_2_rollup(
    scg: nx.DiGraph,
    instances_dict: dict,
) -> None:
    """
    Build up set of sequences for classifiers by taking the union of sequences already generated for the classifier
    subclasses.
    :param lpg: Active SysML graph
    :param scg: Subclassing Graph projection from the LPG
    :param instances_dict: Working dictionary of interpreted sequences for the model
    :return: None - side effect is addition of new instances to the instances dictionary
    """

    roots = [node for node in scg.nodes if scg.in_degree(node) == 0]

    for root in roots:
        bfs_dict = dict(nx.bfs_successors(scg, root))
        bfs_list = list(bfs_dict.keys())
        bfs_list.reverse()

        for gen in bfs_list:
            new_superset = []
            # use the BFS dictionary to be assured that everything is covered
            #update_dict = generate_superset_instances(scg, gen, visited_nodes, instances_dict)

            for subset_node in bfs_dict[gen]:
                new_superset.extend(instances_dict[subset_node])

            instances_dict.update({gen: new_superset})


def random_generator_playbook_phase_2_unconnected(
    all_elements: dict,
    instances_dict: dict,
) -> None:
    """
    Final pass to generate sequences for classifiers that haven't been given sequences yet
    :param all_elements: Full dictionary of elements in the working memory
    :param instances_dict: Working dictionary of interpreted sequences for the model
    :return: None - side effect is addition of new instances to the instances dictionary
    """

    finishing_list = [
        node
        for node in all_elements.values()
        if node["@type"] == "PartDefinition"
           and node["@id"] not in instances_dict
    ]

    for element in finishing_list:
        new_instances = create_set_with_new_instances(
            sequence_template=[element],
            quantities=[1],
            name_hints=[],
        )

        instances_dict.update({element["@id"]: new_instances})


def random_generator_playbook_phase_3(
    feature_sequences: list,
    all_elements: dict,
    lpg: SysML2LabeledPropertyGraph,
    instances_dict: dict,
) -> None:
    """
    Begin generating interpreting sequences for Features in the model by extending classifier sequences with randomly
    selected instances of classifiers that type nested features
    :param feature_sequences: Sequences that represent the nesting structure of the features
    :param all_elements: Full dictionary of elements in the working memory
    :param lpg: Active SysML graph
    :param ptg: Part Typing Graph projection from the LPG
    :param instances_dict: Working dictionary of interpreted sequences for the model
    :return: None - side effect is addition of new instances to the instances dictionary
    """

    already_drawn, last_sequence = {}, []
    for feature_sequence in feature_sequences:
        new_sequences = []

        feat = None
        for index, feature_id in enumerate(feature_sequence):
            if feature_id in instances_dict and index > 0:
                # don't repeat draws if you encounter the same feature again
                continue
            # sample set will be the last element in the sequence for classifiers
            feature = all_elements[feature_id]
            if feature["@type"] in TYPES_FOR_FEATURING:
                types = get_types_for_feature(lpg, feature["@id"])

                if len(types) == 0:
                    raise NotImplementedError(
                        "Cannot handle untyped features! Tried on "
                        f"{get_label_for_id(feature_id, all_elements)}, "
                        f"id = {feature_id}"
                    )
                elif len(types) > 1:
                    raise NotImplementedError("Cannot handle features with multiple types yet!")
                else:
                    typ = types[0]
            else:
                typ = feature_id

            if index == 0:
                if feature["@type"] in ("PartUsage", "AttributeUsage", "PortUsage", "InterfaceUsage", "ConnectionUsage"):
                    # hack for usage at top
                    new_sequences = [instances_dict[typ][0]]
                    if typ in already_drawn:
                        pass
                    else:
                        new_list = [item for item in new_sequences[0]]
                        already_drawn.update({typ: new_list})
                else:
                    new_sequences = instances_dict[typ]
            else:
                # for step in last_sequence:
                #     for feat in feature_sequence:
                #         if step == feat:
                #             new_sequences = instances_dict[feat]

                if typ in already_drawn:
                    remaining = [
                        item
                        for seq in instances_dict[typ]
                        for item in seq
                        if item not in already_drawn[typ]
                    ]
                else:
                    remaining = [item for seq in instances_dict[typ] for item in seq]

                # print("Calling extend sequences by sampling.....")
                # print("Working feature sequence:")
                # seq_print = []
                # for item in feature_sequence:
                #     seq_print.append(get_label_for_id(item, all_elements))
                # print(seq_print)
                # print("Currently working: " + get_label_for_id(feature_id, all_elements) + " with lower mult = " +
                #       str(feature_multiplicity(feature, all_elements, "lower")) + " and upper mult = " +
                #       str(feature_multiplicity(feature, all_elements, "upper"))
                #       )
                # print("Incoming sequences:")
                # print(new_sequences)

                #print("Instances dict for " + get_label_for_id('eb96afae-0f09-4912-861e-705bb33a4202',
                #                                               all_elements) + " updated with " +
                #      str(instances_dict['eb96afae-0f09-4912-861e-705bb33a4202']) + " and index = " + str(index))

                new_sequences = extend_sequences_by_sampling(
                    new_sequences,
                    feature_multiplicity(feature, all_elements, "lower"),
                    feature_multiplicity(feature, all_elements, "upper"),
                    remaining,
                    False,
                    {},
                    {},
                )

                #print("Instances dict for " + get_label_for_id('eb96afae-0f09-4912-861e-705bb33a4202', all_elements) + " updated with " +
                #      str(instances_dict['eb96afae-0f09-4912-861e-705bb33a4202']) + " and index = " + str(index))

                #print("Extended sequences:")
                #print(new_sequences)

                freshly_drawn = [seq[-1] for seq in new_sequences]
                if typ in already_drawn:
                    already_drawn[typ] += [freshly_drawn]
                else:
                    already_drawn[typ] = freshly_drawn

            instances_dict.update({feature_id: new_sequences})
        last_sequence = feature_sequence


def random_generator_playbook_phase_4(
    expr_sequences: list,
    lpg: SysML2LabeledPropertyGraph,
    instances_dict: dict,
) -> None:
    """
    Generate interpreting sequences for Expressions in the model
    :param expr_sequences: Sequences that represent the membership structure for expressions in the model and the features
        to which expressions provide values
    :param lpg: Active SysML graph
    :param instances_dict: Working dictionary of interpreted sequences for the model
    :return: None - side effect is addition of new instances to the instances dictionary
    """
    all_elements = lpg.nodes

    for expr_seq in expr_sequences:
        new_sequences = []
        # get the featuring type of the first expression
        #print(expr_seq[0])

        seq_featuring_type = safe_get_featuring_type_by_id(lpg, expr_seq[0])
        # FIXME: I don't know what it means for binding connectors to own these expressions, but need to figure out eventually
        if seq_featuring_type["@type"] == "BindingConnector":
            continue
        new_sequences = instances_dict[seq_featuring_type["@id"]]

        for feature_id in expr_seq:
            # sample set will be the last element in the sequence for classifiers
            feature_data = all_elements[feature_id]
            feature_metatype = feature_data["@type"]
            if feature_id in instances_dict:
                new_sequences = instances_dict[feature_id]
            else:
                if any(key in feature_metatype for key in ("Expression", "Literal")):
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
                        feature_data,
                    )
                elif feature_metatype == "Feature":
                    new_sequences = extend_sequences_with_new_value_holder(
                        new_sequences,
                        feature_data["name"],
                        feature_data,
                    )
                else:
                    new_sequences = extend_sequences_by_sampling(
                        new_sequences,
                        1,
                        1,
                        [],
                        True,
                        feature_data,
                        all_elements,
                    )
                instances_dict.update({feature_id: new_sequences})


def random_generator_playbook_phase_5(
    lpg: SysML2LabeledPropertyGraph,
    cug: nx.DiGraph,
    instances_dict: dict
):

    # Generate sequences for connection and interface ends
    for node_id in list(cug.nodes):
        node = lpg.nodes[node_id]
        if node['@type'] in ('ConnectionUsage', 'InterfaceUsage'):

            connector_ends = node["connectorEnd"]

            connector_id = node['@id']

            source_feat_id = node['source'][0]['@id']
            target_feat_id = node['target'][0]['@id']

            source_sequences = instances_dict[source_feat_id]
            target_sequences = instances_dict[target_feat_id]

            connectors = instances_dict[connector_id]

            extended_source_sequences = []
            extended_target_sequences = []

            for indx, seq in enumerate(connectors):
                new_source_seq = []
                new_target_seq = []

                for item in seq:
                    new_source_seq.append(item)
                    new_target_seq.append(item)

                for jndx, item in enumerate(source_sequences[indx]):
                    if jndx > 0:
                        new_source_seq.append(item)

                for jndx, item in enumerate(target_sequences[indx]):
                    if jndx > 0:
                        new_target_seq.append(item)

                extended_source_sequences.append(new_source_seq)
                extended_target_sequences.append(new_target_seq)

            instances_dict.update({connector_ends[0]['@id']: extended_source_sequences})
            instances_dict.update({connector_ends[1]['@id']: extended_target_sequences})


def build_sequence_templates(lpg: SysML2LabeledPropertyGraph) -> list:
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

        # TODO: Look into adding the topologically sorted connected subcomponents
        # sorted_feature_groups.append(
        #     [node for node in nx.topological_sort(connected_sub)]
        # )

    return sorted_feature_groups


def generate_superset_instances(
        part_def_graph: nx.MultiDiGraph,
        superset_node: str,
        visited_nodes: set,
        instances_dict: dict,
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
    evg = lpg.get_projection("Expression Value Graph")

    # FIXME: Need projections to work correctly
    # TODO: @Bjorn: should we remove all the implied edges? We could add a key to them
    to_remove = [
        edge for edge in evg.edges
        if edge[2] == "ImpliedParameterFeedforward"
    ]

    for source, target, *_ in to_remove:
        evg.remove_edge(source, target)

    sorted_feature_groups = []
    for comp in nx.connected_components(evg.to_undirected()):
        connected_sub = nx.subgraph(evg, list(comp))
        leaves = [node for node in connected_sub.nodes if connected_sub.out_degree(node) == 0]
        roots = [node for node in connected_sub.nodes if connected_sub.in_degree(node) == 0]
        for root in roots:
            for leaf in leaves:
                try:
                    leaf_path = nx.shortest_path(connected_sub, root, leaf)
                    sorted_feature_groups.append(leaf_path)
                except:
                    pass

    return sorted_feature_groups


def validate_working_data(lpg: SysML2LabeledPropertyGraph) -> bool:
    """
    Helper method to check that the user model is valid for instance generation
    :return: A Boolean indicating that the user model is ready to be interpreted
    """

    # check that all the elements of the graph are in fact proper model elements

    all_non_relations = lpg.nodes
    for nr_key, nr in all_non_relations.items():
        try:
            nr_type = nr["@type"]
        except KeyError:
            print(f"No type found in {nr}, id = '{nr_key}'")
            return False
        except TypeError:
            print(f"Expecting dict of model element data, got = {nr}")
        if "@id" not in nr:
            print(f"No '@id' found in {nr}, id = '{nr_key}'")
            return False

    return True
