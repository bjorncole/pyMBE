from ..fixtures.data_loader import kerbal_model_loaded_client
from pymbe.graph.lpg import SysML2LabeledPropertyGraph
from pymbe.client import SysML2Client
from pymbe.interpretation.interp_playbooks import *
from pymbe.interpretation.set_builders import *
import pytest

# there must be a way to reuse from other modules ..
@pytest.fixture
def kerbal_client() -> SysML2Client:

    return kerbal_model_loaded_client()


@pytest.fixture
def kerbal_ids_by_type(kerbal_client) -> dict:

    ids_dict = {}

    all_elements = kerbal_client.elements_by_id

    for ele_id, ele in all_elements.items():
        if ele["@type"] in ids_dict:
            ids_dict[ele["@type"]].append(ele_id)
        else:
            ids_dict.update({ele['@type']: [ele_id]})

    return ids_dict


@pytest.fixture
def kerbal_lpg() -> SysML2LabeledPropertyGraph:
    new_lpg = SysML2LabeledPropertyGraph()
    client = kerbal_model_loaded_client()

    new_lpg.update(client.elements_by_id, False)

    return new_lpg


@pytest.fixture
def random_stage_1_instances(kerbal_client, kerbal_lpg) -> dict:
    ptg = kerbal_lpg.get_projection("Part Typing Graph")
    scg = kerbal_lpg.get_projection("Part Definition Graph")

    flea_id = '68f08797-0e68-47b1-bad5-9e734af2742f'

    random_generator_phase_0_interpreting_edges(kerbal_client, kerbal_lpg)

    full_multiplicities = random_generator_phase_1_multiplicities(kerbal_lpg, ptg, scg)

    instances_dict = {}

    for type_id, number in full_multiplicities.items():
        new_instances = create_set_with_new_instances(
            sequence_template=[kerbal_lpg.nodes[type_id]],
            quantities=[number],
            name_hints=[],
        )

        instances_dict.update({type_id: new_instances})

    return instances_dict


@pytest.fixture
def random_stage_1_complete(kerbal_lpg, random_stage_1_instances) -> dict:
    scg = kerbal_lpg.get_projection("Part Definition Graph")

    random_generator_playbook_phase_1_singletons(
        kerbal_lpg,
        scg,
        random_stage_1_instances
    )

    return random_stage_1_instances


@pytest.fixture
def random_stage_2_complete(kerbal_lpg, random_stage_1_complete) -> dict:
    scg = kerbal_lpg.get_projection("Part Definition Graph")

    random_generator_playbook_phase_2_rollup(kerbal_lpg, scg, random_stage_1_complete)

    random_generator_playbook_phase_2_unconnected(kerbal_lpg.nodes, random_stage_1_complete)

    return random_stage_1_complete


@pytest.fixture
def random_stage_3_complete(kerbal_lpg, random_stage_2_complete) -> dict:
    ptg = kerbal_lpg.get_projection("Part Typing Graph")
    all_elements = kerbal_lpg.nodes
    feature_sequences = build_sequence_templates(lpg=kerbal_lpg)

    random_generator_playbook_phase_3(feature_sequences, all_elements, ptg, random_stage_2_complete)

    return random_stage_2_complete


@pytest.fixture
def random_stage_4_complete(kerbal_lpg, random_stage_3_complete) -> dict:

    expr_sequences = build_expression_sequence_templates(lpg=kerbal_lpg)

    random_generator_playbook_phase_4(expr_sequences, kerbal_lpg, random_stage_3_complete)

    return random_stage_3_complete


def test_type_multiplicity_dict_building(kerbal_lpg):

    solid_stage_id = '818da4ef-ebf0-409d-873f-77beacbae681'
    liquid_stage_id = '6c18b7a9-8bf9-49ff-87c5-a53dd73aeb58'
    flea_id = '68f08797-0e68-47b1-bad5-9e734af2742f'
    hammer_id = '628929a4-1dc2-4c34-aefb-2653faaa46fe'
    f100_tank = '2abf7097-1621-4264-a5d3-4b7aa3819a24'
    f200_tank = 'c94930cd-8cb4-43f6-9986-90341e85e66b'

    ptg = kerbal_lpg.get_projection("Part Typing Graph")
    scg = kerbal_lpg.get_projection("Part Definition Graph")

    full_multiplicities = random_generator_phase_1_multiplicities(kerbal_lpg, ptg, scg)

    assert len(full_multiplicities) == 8
    assert full_multiplicities[solid_stage_id] + full_multiplicities[liquid_stage_id] == 5
    assert full_multiplicities[flea_id] + full_multiplicities[hammer_id] == 40
    assert full_multiplicities[f100_tank] + full_multiplicities[f200_tank] == 150


def test_phase_0_implied_relationships(kerbal_client, kerbal_lpg):

    random_generator_phase_0_interpreting_edges(kerbal_client, kerbal_lpg)

    all_edge_keys = list(kerbal_lpg.edges.keys())
    all_edge_types = [edg[2] for edg in all_edge_keys]
    implied_edges = [edg for edg in all_edge_keys if edg[2] == 'ImpliedParameterFeedforward']

    assert any([typ == 'ImpliedParameterFeedforward' for typ in all_edge_types])
    assert len(implied_edges) == 10


def test_phase_1_instance_creation(random_stage_1_instances):

    flea_id = '68f08797-0e68-47b1-bad5-9e734af2742f'
    solid_stage_id = '818da4ef-ebf0-409d-873f-77beacbae681'
    solid_booster_id = 'e4cee07b-5813-4214-8ee7-e9d3d05a4d62'

    assert flea_id in random_stage_1_instances
    assert solid_stage_id in random_stage_1_instances
    # don't expect abstract member at this point
    assert solid_booster_id not in random_stage_1_instances


def test_phase_1_singleton_instances(random_stage_1_complete):
    flea_id = '68f08797-0e68-47b1-bad5-9e734af2742f'
    solid_stage_id = '818da4ef-ebf0-409d-873f-77beacbae681'
    solid_booster_id = 'e4cee07b-5813-4214-8ee7-e9d3d05a4d62'
    pod_id = '4594d3d3-f76f-435a-a68f-092237f0c241'

    assert flea_id in random_stage_1_complete
    assert solid_stage_id in random_stage_1_complete
    assert pod_id in random_stage_1_complete
    # don't expect abstract member at this point
    assert solid_booster_id not in random_stage_1_complete

def test_phase_2_instance_creation(kerbal_lpg, random_stage_1_complete):
    solid_stage_id = '818da4ef-ebf0-409d-873f-77beacbae681'
    liquid_stage_id = '6c18b7a9-8bf9-49ff-87c5-a53dd73aeb58'
    flea_id = '68f08797-0e68-47b1-bad5-9e734af2742f'
    pod_id = '86329d0b-c6cb-49a7-b780-8ad2d2401ea6'
    krp_id = '63f5c455-261b-4a80-9a3b-5a9bef2361da'
    solid_booster_id = 'e4cee07b-5813-4214-8ee7-e9d3d05a4d62'
    rocket_id = '4c792c29-5fd0-4846-b4e5-800a0bc037f1'

    scg = kerbal_lpg.get_projection("Part Definition Graph")

    random_generator_playbook_phase_2_rollup(kerbal_lpg, scg, random_stage_1_complete)

    random_generator_playbook_phase_2_unconnected(kerbal_lpg.nodes, random_stage_1_complete)

    assert flea_id in random_stage_1_complete
    assert pod_id in random_stage_1_complete
    assert krp_id in random_stage_1_complete
    assert solid_booster_id in random_stage_1_complete
    assert rocket_id in random_stage_1_complete

    assert len(random_stage_1_complete[solid_stage_id]) + \
           len(random_stage_1_complete[liquid_stage_id]) == 5
    assert len(random_stage_1_complete[solid_booster_id]) == 40

    assert len(random_stage_1_complete[krp_id]) == 272


def test_phase_3_instance_sampling(kerbal_lpg, random_stage_3_complete):
    coupler_usage_id = '7a7bd380-1dde-4544-bcd6-187f0f5b6d20'

    assert coupler_usage_id in random_stage_3_complete
    assert len(random_stage_3_complete[coupler_usage_id]) == 0 or len(random_stage_3_complete[coupler_usage_id][0]) == 3


def test_phase_4_instance_sampling(kerbal_lpg, random_stage_4_complete):
    top_plus_expr_id = 'd05c42b2-3453-4c94-bf18-5bbc38949d19'
    sum_1_id = '64d50fe9-ab5c-42b4-9968-4988101da642'
    collect_1_id = '30cb30dd-1a08-4da8-8274-3e397df281de'
    collect_1_result = '243251f8-0b65-48b2-8fbb-8a3ce502f41f'

    liquid_stage_id = '6c18b7a9-8bf9-49ff-87c5-a53dd73aeb58'

    assert len(random_stage_4_complete[collect_1_id]) > 0 or \
        len(random_stage_4_complete[liquid_stage_id]) == 0

    assert len(random_stage_4_complete[collect_1_result]) > 0 or \
           len(random_stage_4_complete[liquid_stage_id]) == 0


# should move these to a separate file but need the common fixtures
def test_new_instances(kerbal_lpg):
    part_defs = kerbal_lpg.nodes_by_type['PartDefinition']

    new_instances = {}

    for part_def in part_defs:
        new_instances[part_def] = create_set_with_new_instances(
            sequence_template=[kerbal_lpg.nodes[part_def]],
            quantities=[10],
            name_hints=[],
        )

    assert len(new_instances) == 17


def test_instance_sampling(kerbal_lpg):
    # what we really need here is a fixture that generates a healthy instance dictionary from the playbook phases

    solid_booster_id = '818da4ef-ebf0-409d-873f-77beacbae681'
    boosters_id = 'a75c2967-b3ef-4434-8c0f-5f708b96711c'
    liquid_stage_id = '6c18b7a9-8bf9-49ff-87c5-a53dd73aeb58'
    engines_id = '48e94e73-52ad-44df-8005-8fa6225176d8'
    tanks_id = 'ae3db8b5-6d8e-4ac4-af46-9f37ad0fd988'

    # try creating the boosters under solid stage

    solid_stage_instances = create_set_with_new_instances(
        sequence_template=[kerbal_lpg.nodes[solid_booster_id]],
        quantities=[5],
        name_hints=[],
    )

    solid_booster_instances = create_set_with_new_instances(
        sequence_template=[kerbal_lpg.nodes[solid_booster_id]],
        quantities=[40],
        name_hints=[],
    )

    booster_feature_instances = extend_sequences_by_sampling(
        solid_stage_instances,
        8,
        8,
        solid_booster_instances,
        False,
        {},
        {}
    )

    assert len(booster_feature_instances) == 40
    assert len(booster_feature_instances[4]) == 2