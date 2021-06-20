import networkx as nx

from pymbe.interpretation.interp_playbooks import (
    random_generator_phase_0_interpreting_edges,
    random_generator_phase_1_multiplicities,
    random_generator_playbook_phase_2_rollup,
    random_generator_playbook_phase_2_unconnected,
)
from pymbe.interpretation.set_builders import (
    create_set_with_new_instances,
    extend_sequences_by_sampling,
)


def test_type_multiplicity_dict_building(kerbal_lpg):
    solid_stage_id = "b473978d-40de-4809-acef-4793f738c44e"
    liquid_stage_id = "e6c22f19-e5e0-4a4b-9a3f-af2f01382465"
    flea_id = "5be56a39-f4a4-4fbb-872c-12f3e717593c"
    hammer_id = "8851ab1c-0d7f-4fe2-bee0-8b29d408c897"
    f100_tank = "1eca9960-e445-4d2f-be3f-cd7a6882435d"
    f200_tank = "cc585eec-c66c-48aa-b319-1395a0c8e292"
    real_id = "ede2b2e7-9280-4932-9453-134bf460892f"

    ptg = kerbal_lpg.get_projection("Part Typing Graph")
    scg = kerbal_lpg.get_projection("Part Definition Graph")

    full_multiplicities = random_generator_phase_1_multiplicities(kerbal_lpg, ptg, scg)

    assert len(full_multiplicities) == 9
    assert full_multiplicities[solid_stage_id] + full_multiplicities[liquid_stage_id] == 5
    assert full_multiplicities[flea_id] + full_multiplicities[hammer_id] == 40
    assert full_multiplicities[f100_tank] + full_multiplicities[f200_tank] == 150
    assert full_multiplicities[real_id] == 3010


def test_phase_0_implied_relationships(kerbal_client, kerbal_lpg):
    random_generator_phase_0_interpreting_edges(kerbal_client, kerbal_lpg)

    all_edge_keys = list(kerbal_lpg.edges.keys())
    all_edge_types = [edg[2] for edg in all_edge_keys]
    implied_edges = [edg for edg in all_edge_keys if edg[2] == "ImpliedParameterFeedforward"]

    assert any([typ == "ImpliedParameterFeedforward" for typ in all_edge_types])
    assert len(implied_edges) == 30


def test_phase_1_instance_creation(kerbal_random_stage_1_instances):
    flea_id = "5be56a39-f4a4-4fbb-872c-12f3e717593c"
    solid_stage_id = "b473978d-40de-4809-acef-4793f738c44e"
    solid_booster_id = "24a0a10e-77ba-4bfa-9618-f2525a8a7042"
    real_id = "ede2b2e7-9280-4932-9453-134bf460892f"

    assert flea_id in kerbal_random_stage_1_instances
    assert solid_stage_id in kerbal_random_stage_1_instances
    assert real_id in kerbal_random_stage_1_instances
    # don"t expect abstract member at this point
    assert solid_booster_id not in kerbal_random_stage_1_instances


def test_phase_1_singleton_instances(kerbal_random_stage_1_complete):
    flea_id = "5be56a39-f4a4-4fbb-872c-12f3e717593c"
    solid_stage_id = "b473978d-40de-4809-acef-4793f738c44e"
    solid_booster_id = "24a0a10e-77ba-4bfa-9618-f2525a8a7042"
    pod_id = "62f8fd9a-6b7e-4af1-9fad-52641da6c854"

    assert flea_id in kerbal_random_stage_1_complete
    assert solid_stage_id in kerbal_random_stage_1_complete
    assert pod_id in kerbal_random_stage_1_complete
    # don"t expect abstract member at this point
    assert solid_booster_id not in kerbal_random_stage_1_complete


def test_phase_2_instance_creation(kerbal_lpg, kerbal_random_stage_1_complete):
    solid_stage_id = "b473978d-40de-4809-acef-4793f738c44e"
    liquid_stage_id = "e6c22f19-e5e0-4a4b-9a3f-af2f01382465"
    flea_id = "5be56a39-f4a4-4fbb-872c-12f3e717593c"
    pod_id = "62f8fd9a-6b7e-4af1-9fad-52641da6c854"
    krp_id = "f2d4d0c1-83dd-41c0-848a-fc00d4bc99d6"
    solid_booster_id = "24a0a10e-77ba-4bfa-9618-f2525a8a7042"
    rocket_id = "62fc7eb7-0637-4201-add7-4d2758980d2f"

    scg = kerbal_lpg.get_projection("Part Definition Graph")

    random_generator_playbook_phase_2_rollup(kerbal_lpg, scg, kerbal_random_stage_1_complete)

    random_generator_playbook_phase_2_unconnected(kerbal_lpg.nodes, kerbal_random_stage_1_complete)

    assert flea_id in kerbal_random_stage_1_complete
    assert pod_id in kerbal_random_stage_1_complete
    assert krp_id in kerbal_random_stage_1_complete
    assert solid_booster_id in kerbal_random_stage_1_complete
    assert rocket_id in kerbal_random_stage_1_complete

    assert len(kerbal_random_stage_1_complete[solid_stage_id]) + \
           len(kerbal_random_stage_1_complete[liquid_stage_id]) == 5
    assert len(kerbal_random_stage_1_complete[solid_booster_id]) == 40

    assert len(kerbal_random_stage_1_complete[krp_id]) == 272


def test_phase_3_instance_sampling(kerbal_lpg, kerbal_random_stage_3_complete):
    coupler_usage_id = "3a609e5a-3e6f-4eb4-97ff-5a32b23122bf"

    booster_empty_mass_id = "645ee1b3-3cb3-494e-8cb2-ec32e377c9f6"
    booster_isp_id = "2b1351f4-a0fb-470b-bb22-1b924dde38f7"
    rt_10_isp_id = "eb09ff1c-1791-4571-8016-c0534906faa4"

    print(kerbal_random_stage_3_complete[coupler_usage_id][0])

    assert coupler_usage_id in kerbal_random_stage_3_complete
    assert len(kerbal_random_stage_3_complete[coupler_usage_id]) == 0 or \
           len(kerbal_random_stage_3_complete[coupler_usage_id][0]) == 3

    assert len(kerbal_random_stage_3_complete[booster_isp_id]) > 0
    assert len(kerbal_random_stage_3_complete[rt_10_isp_id]) > 0
    assert len(kerbal_random_stage_3_complete[booster_empty_mass_id]) > 0


def test_phase_4_instance_sampling(kerbal_lpg, kerbal_random_stage_4_complete):
    top_plus_expr_id = "b51bb349-e210-4be8-be64-e749ea4e563b"
    sum_1_id = "700d97d1-410a-459c-ad09-8792c27e2803"
    collect_1_id = "d6644a0a-6eef-49c1-a770-60886073554c"
    collect_1_result = "31f8c4bd-9700-4bc3-9970-3eb5451f0203"

    liquid_stage_id = "e6c22f19-e5e0-4a4b-9a3f-af2f01382465"

    booster_empty_mass_id = "645ee1b3-3cb3-494e-8cb2-ec32e377c9f6"
    booster_isp_id = "2b1351f4-a0fb-470b-bb22-1b924dde38f7"
    rt_10_isp_id = "eb09ff1c-1791-4571-8016-c0534906faa4"

    assert len(kerbal_random_stage_4_complete[collect_1_id]) > 0 or \
        len(kerbal_random_stage_4_complete[liquid_stage_id]) == 0

    assert len(kerbal_random_stage_4_complete[collect_1_result]) > 0 or \
           len(kerbal_random_stage_4_complete[liquid_stage_id]) == 0

    if len(kerbal_random_stage_4_complete[liquid_stage_id]) > 0:
        assert len(kerbal_random_stage_4_complete[top_plus_expr_id][0]) == 2

    if len(kerbal_random_stage_4_complete[liquid_stage_id]) > 0:
        assert len(kerbal_random_stage_4_complete[sum_1_id][0]) == 3

    assert len(kerbal_random_stage_4_complete[booster_isp_id]) > 0
    assert len(kerbal_random_stage_4_complete[rt_10_isp_id]) > 0
    assert len(kerbal_random_stage_4_complete[booster_empty_mass_id]) > 0


def test_expression_inferred_graph(kerbal_client, kerbal_lpg):
    # inferred graph provides a reliable order of execution for expressions
    random_generator_phase_0_interpreting_edges(kerbal_client, kerbal_lpg)

    all_edge_keys = list(kerbal_lpg.edges.keys())
    all_edge_types = [edg[2] for edg in all_edge_keys]
    implied_edges = [edg for edg in all_edge_keys if edg[2] == "ImpliedParameterFeedforward"]

    assert any([typ == "ImpliedParameterFeedforward" for typ in all_edge_types])
    assert len(implied_edges) == 30

    eig = kerbal_lpg.get_projection("Expression Inferred Graph")

    top_plus_expr_id = "d05c42b2-3453-4c94-bf18-5bbc38949d19"
    fl_200_full_mass_id = "c3344ffd-6a7f-499b-90cf-e7e311e309f5"
    x_feature = "1159649f-b211-42c1-84e7-0bf3fc88417f"
    deep_mass_feature = "0bc0b127-ffcb-44a8-ad65-2c34745e9b2d"

    for comp in nx.connected_components(eig.to_undirected()):
        connected_sub = nx.subgraph(eig, list(comp))
        if top_plus_expr_id in list(comp):
            assert len(list(comp)) == 44


def test_dependency_graph(kerbal_lpg, kerbal_random_stage_4_complete):
    # see how fully solved sequences go to make the dependency graph for computation
    assert True


# should move these to a separate file but need the common fixtures
def test_new_instances(kerbal_lpg):
    part_defs = kerbal_lpg.nodes_by_type["PartDefinition"]

    new_instances = {}

    for part_def in part_defs:
        new_instances[part_def] = create_set_with_new_instances(
            sequence_template=[kerbal_lpg.nodes[part_def]],
            quantities=[10],
            name_hints={},
        )

    assert len(new_instances) == 17


def test_instance_sampling(kerbal_lpg):
    # what we really need here is a fixture that generates a healthy instance dictionary from the playbook phases
    solid_booster_id = "24a0a10e-77ba-4bfa-9618-f2525a8a7042"

    # try creating the boosters under solid stage

    solid_stage_instances = create_set_with_new_instances(
        sequence_template=[kerbal_lpg.nodes[solid_booster_id]],
        quantities=[5],
        name_hints={},
    )

    solid_booster_instances = create_set_with_new_instances(
        sequence_template=[kerbal_lpg.nodes[solid_booster_id]],
        quantities=[40],
        name_hints={},
    )

    booster_feature_instances = extend_sequences_by_sampling(
        solid_stage_instances,
        8,
        8,
        solid_booster_instances,
        False,
        {},
        {},
    )

    assert len(booster_feature_instances) == 40
    assert len(booster_feature_instances[4]) == 2
