from pathlib import Path

import pytest

from pymbe.client import SysML2Client
from pymbe.interpretation.interp_playbooks import *
from pymbe.interpretation.set_builders import *


TEST_ROOT = Path(__file__).parent


def kerbal_model_loaded_client() -> SysML2Client:
    helper_client = SysML2Client()
    file_name = TEST_ROOT / "data/Kerbal/elements.json"
    helper_client._load_disk_elements(file_name)

    return helper_client


def simple_parts_model_loaded_client() -> SysML2Client:
    helper_client = SysML2Client()
    file_name = TEST_ROOT / "data/Simple Parts Model/elements.json"
    helper_client._load_disk_elements(file_name)

    return helper_client


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
            ids_dict.update({ele["@type"]: [ele_id]})

    return ids_dict


@pytest.fixture
def kerbal_lpg() -> SysML2LabeledPropertyGraph:
    new_lpg = SysML2LabeledPropertyGraph()
    client = kerbal_model_loaded_client()

    new_lpg.update(client.elements_by_id, False)

    return new_lpg


@pytest.fixture
def kerbal_random_stage_1_instances(kerbal_client, kerbal_lpg) -> dict:
    ptg = kerbal_lpg.get_projection("Part Typing Graph")
    scg = kerbal_lpg.get_projection("Part Definition Graph")

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
def kerbal_random_stage_1_complete(kerbal_lpg, random_stage_1_instances) -> dict:
    scg = kerbal_lpg.get_projection("Part Definition Graph")

    random_generator_playbook_phase_1_singletons(
        kerbal_lpg,
        scg,
        random_stage_1_instances
    )

    return random_stage_1_instances


@pytest.fixture
def kerbal_random_stage_2_complete(kerbal_lpg, random_stage_1_complete) -> dict:
    scg = kerbal_lpg.get_projection("Part Definition Graph")

    random_generator_playbook_phase_2_rollup(kerbal_lpg, scg, random_stage_1_complete)

    random_generator_playbook_phase_2_unconnected(kerbal_lpg.nodes, random_stage_1_complete)

    return random_stage_1_complete


@pytest.fixture
def kerbal_random_stage_3_complete(kerbal_lpg, random_stage_2_complete) -> dict:
    ptg = kerbal_lpg.get_projection("Part Typing Graph")
    all_elements = kerbal_lpg.nodes
    feature_sequences = build_sequence_templates(lpg=kerbal_lpg)

    random_generator_playbook_phase_3(feature_sequences, all_elements, ptg, random_stage_2_complete)

    return random_stage_2_complete


@pytest.fixture
def kerbal_random_stage_4_complete(kerbal_lpg, random_stage_3_complete) -> dict:

    expr_sequences = build_expression_sequence_templates(lpg=kerbal_lpg)

    random_generator_playbook_phase_4(expr_sequences, kerbal_lpg, random_stage_3_complete)

    return random_stage_3_complete
