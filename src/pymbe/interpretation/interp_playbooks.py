from uuid import uuid4

from .set_builders import *
from ..query.query import *

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

    random_generator_playbook_phase_2_rollup(
        lpg,
        scg,
        instances_dict
    )

    # Fill in any part definitions that still don't have instances yet (because they get filtered out by the
    # Part Definition pre-defined graph (neither typed nor subclassed))

    random_generator_playbook_phase_2_unconnected(all_elements, instances_dict)

    # PHASE 3: Expand the dictionaries out into feature sequences by pulling from instances developed here

    random_generator_playbook_phase_3(feature_sequences, all_elements, ptg, instances_dict)

    # PHASE 4: Expand sequences to support computations

    expr_sequences = build_expression_sequence_templates(lpg=lpg)

    # for indx, seq in enumerate(expr_sequences):
    #    print("Sequence number " + str(indx))
    #    for item in seq:
    #        print(get_label(all_elements[item], all_elements) + ", id = " + item)

    # Move through existing sequences and then start to pave further with new steps

    random_generator_playbook_phase_4(expr_sequences, lpg, instances_dict)

    return instances_dict


def random_generator_phase_0_interpreting_edges(
    lpg: SysML2LabeledPropertyGraph
):
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
    for edg in new_edges:
        new_edg = {(edg[0:3]): edg[3]}
        lpg.edges.update(new_edg)

    lpg.graph.add_edges_from([
            [
                edg[0],  # source node (str id)
                edg[1],  # target node (str id)
                edg[2],  # edge type (str name)
                edg[3],  # edge data (dict)
            ]
            for edg in new_edges
        ])


def random_generator_phase_1_multiplicities(
    lpg: SysML2LabeledPropertyGraph,
    ptg: nx.DiGraph,
    scg: nx.DiGraph
) -> dict:
    # will sub-divide abstract multiplicity
    abstracts = [
        node
        for node in ptg.nodes
        if lpg.nodes.get(node, {}).get("isAbstract")
    ]

    # find the maximal amount of types directly based on instances
    type_multiplicities = {}
    for pt in ptg.nodes:
        if lpg.nodes[pt]['@type'] in ('PartDefinition', 'DataType', 'AttributeDefinition'):
            mult = roll_up_multiplicity_for_type(
                lpg,
                lpg.nodes[pt],
                "upper"
            )
            type_multiplicities.update({pt: mult})

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
                    draw = random.randint(0, mult)
                    taken = taken + draw
                else:
                    draw = mult - taken
                full_multiplicities.update({specific: draw})
        else:
            full_multiplicities.update({typ: mult})

    return full_multiplicities


def random_generator_playbook_phase_1_singletons(
    lpg: SysML2LabeledPropertyGraph,
    scg: nx.DiGraph,
    instances_dict: dict
) -> None:
    all_elements = lpg.nodes

    # need to generate single instances at leaves that don't match types
    leaves = [node for node in scg.nodes if scg.out_degree(node) == 0]

    for leaf in leaves:
        if leaf not in instances_dict:
            new_instances = create_set_with_new_instances(
                sequence_template=[all_elements[leaf]],
                quantities=[1],
                name_hints=[],
            )

            instances_dict.update({leaf: new_instances})


def random_generator_playbook_phase_2_rollup(
    lpg: SysML2LabeledPropertyGraph,
    scg: nx.DiGraph,
    instances_dict: dict
) -> None:
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
    instances_dict: dict
) -> None:

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
            name_hints=[],
        )

        instances_dict.update({element["@id"]: new_instances})


def random_generator_playbook_phase_3(
    feature_sequences: list,
    all_elements: dict,
    ptg: nx.DiGraph,
    instances_dict: dict
) -> None:
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
            if feature["@type"] in ("PartUsage", "AttributeUsage"):
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

                for step in last_sequence:
                    for feat in feature_sequence:
                        if step == feat:
                            new_sequences = instances_dict[feat]

                if typ in already_drawn:
                    remaining = [item for seq in instances_dict[typ] for item in seq if item not in already_drawn[typ]]
                else:
                    remaining = [item for seq in instances_dict[typ] for item in seq]

                new_sequences = extend_sequences_by_sampling(
                    new_sequences,
                    feature_multiplicity(feature, all_elements, "lower"),
                    feature_multiplicity(feature, all_elements, "upper"),
                    remaining,
                    False,
                    {},
                    {}
                )

                freshly_drawn = [seq[-1] for seq in new_sequences]
                if typ in already_drawn:
                    already_drawn[typ].extend(freshly_drawn)
                else:
                    already_drawn.update({typ: freshly_drawn})

            instances_dict.update({feature_id: new_sequences})

        last_sequence = feature_sequence


def random_generator_playbook_phase_4(
    expr_sequences: list,
    lpg: SysML2LabeledPropertyGraph,
    instances_dict: dict
) -> None:
    all_elements = lpg.nodes
    for expr_seq in expr_sequences:
        new_sequences = []
        # get the featuring type of the first expression

        seq_featuring_type = safe_get_featuring_type_by_id(lpg, expr_seq[0])
        new_sequences = instances_dict[seq_featuring_type['@id']]

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

    # FIXME: Need projections to work correctly

    to_remove = [
        edg
        for edg in evg.edges
        if edg[2] == "ImpliedParameterFeedforward"
    ]

    for remover in to_remove:
        evg.remove_edge(remover[0], remover[1])

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
