import pytest

from pymbe.client import SysML2Client
from pymbe.graph.lpg import SysML2LabeledPropertyGraph
from pymbe.interpretation.interp_playbooks import (
    build_expression_sequence_templates,
    build_sequence_templates,
    random_generator_phase_0_interpreting_edges,
)

from ..data_loader import kerbal_model_loaded_client


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

    assert len(seq_templates) == 39

    solid_booster_id = '818da4ef-ebf0-409d-873f-77beacbae681'
    boosters_id = 'a75c2967-b3ef-4434-8c0f-5f708b96711c'
    liquid_stage_id = '6c18b7a9-8bf9-49ff-87c5-a53dd73aeb58'
    engines_id = '48e94e73-52ad-44df-8005-8fa6225176d8'
    tanks_id = 'ae3db8b5-6d8e-4ac4-af46-9f37ad0fd988'
    krp_mass_id = 'f0403f3c-b5b8-4d2e-814b-bbe7cff60d3f'

    rocket_id = '62fc7eb7-0637-4201-add7-4d2758980d2f'
    stages_feature_id = '442722b5-8d08-46e4-ad5f-e6e2dd28d6f6'
    couple_feature_id = '3a609e5a-3e6f-4eb4-97ff-5a32b23122bf'

    print(seq_templates)

    assert [
        '62fc7eb7-0637-4201-add7-4d2758980d2f',
        '442722b5-8d08-46e4-ad5f-e6e2dd28d6f6',
        '3a609e5a-3e6f-4eb4-97ff-5a32b23122bf',
        '7f5e38cb-6647-482d-b8fe-5c266d73ab42'] in seq_templates

    assert(any([krp_mass_id in seq for seq in seq_templates]))

    for seq in seq_templates:
        if solid_booster_id in seq:
            assert boosters_id in seq
        if liquid_stage_id in seq:
            assert (engines_id in seq or tanks_id in seq)
            if engines_id in seq:
                assert seq.index(liquid_stage_id) < seq.index(engines_id)
            elif tanks_id in seq:
                assert seq.index(liquid_stage_id) < seq.index(tanks_id)


def test_expression_sequence_templates(kerbal_client, kerbal_lpg):

    fts_full_mass = '004a1b5f-4bfc-4460-9f38-1e7b4caba6e5'
    ft200_full_mass = '1e5a0ed7-8b41-4ab4-a433-8f7eedd75833'
    ft100_full_mass = 'a57b423b-5c0c-4057-be6b-689abcb536b2'
    liquid_stage_full_mass = '7beafac8-c1c1-4b1b-ae21-d3c9a733531c'
    top_plus = 'b51bb349-e210-4be8-be64-e749ea4e563b'
    tank_mass_sum_1 = '700d97d1-410a-459c-ad09-8792c27e2803'
    collect_1 = 'd6644a0a-6eef-49c1-a770-60886073554c'
    collect_1_result = '31f8c4bd-9700-4bc3-9970-3eb5451f0203'
    full_mass_dot = 'ad0bff53-eebe-4446-a8df-4db0b7187707'
    fre_1 = '2665fb1b-1f12-4f13-a977-0f060915773e'
    fre_1_result = '6cfb516b-6045-454e-a521-83b747acef7e'

    random_generator_phase_0_interpreting_edges(kerbal_client, kerbal_lpg)

    expr_sequences = build_expression_sequence_templates(lpg=kerbal_lpg)
    top_plus_paths = 0
    direct_literals = 0

    fre_result_found = False

    # big roll-up
    for seq in expr_sequences:
        if top_plus in seq:
            top_plus_paths += 1
        if fre_1_result in seq:
            fre_result_found = True

    # individual literal expression value assignments
    for seq in expr_sequences:
        if 'Literal' in kerbal_lpg.nodes[seq[0]]['@type']:
            direct_literals += 1
            assert len(seq) == 2
        # each sequence should end with the result
        assert kerbal_lpg.nodes[seq[len(seq) - 1]]['@type'] == 'Feature'

    assert top_plus_paths == 17
    assert direct_literals == 26
    assert len(expr_sequences) == 43

    assert fre_result_found
