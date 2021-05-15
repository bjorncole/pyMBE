from ..fixtures.data_loader import kerbal_model_loaded_client
from pymbe.graph.lpg import SysML2LabeledPropertyGraph
from pymbe.client import SysML2Client
from pymbe.interpretation.interp_playbooks import build_sequence_templates
import pytest
import networkx as nx

# there must be a way to reuse from other modules ..
@pytest.fixture
def kerbal_client() -> SysML2Client:

    return kerbal_model_loaded_client()


@pytest.fixture()
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


def test_feature_sequence_templates(kerbal_client, kerbal_lpg):

    seq_templates = build_sequence_templates(kerbal_lpg)

    assert len(seq_templates) == 4

    solid_booster_id = '818da4ef-ebf0-409d-873f-77beacbae681'
    boosters_id = 'a75c2967-b3ef-4434-8c0f-5f708b96711c'
    liquid_stage_id = '6c18b7a9-8bf9-49ff-87c5-a53dd73aeb58'
    engines_id = '48e94e73-52ad-44df-8005-8fa6225176d8'
    tanks_id = 'ae3db8b5-6d8e-4ac4-af46-9f37ad0fd988'

    for seq in seq_templates:
        if solid_booster_id in seq:
            assert boosters_id in seq
        if liquid_stage_id in seq:
            assert (engines_id in seq or tanks_id in seq)
            if engines_id in seq:
                assert seq.index(liquid_stage_id) < seq.index(engines_id)
            elif tanks_id in seq:
                assert seq.index(liquid_stage_id) < seq.index(tanks_id)