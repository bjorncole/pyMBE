from ..data_loader import kerbal_model_loaded_client
from pymbe.graph.lpg import SysML2LabeledPropertyGraph
from pymbe.client import SysML2Client
from pymbe.query.query import *
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
def kerbal_lpg(kerbal_client) -> SysML2LabeledPropertyGraph:
    new_lpg = SysML2LabeledPropertyGraph()

    new_lpg.update(kerbal_client.elements_by_id, False)

    return new_lpg

def test_feature_multiplicity_rollup(kerbal_client, kerbal_lpg):

    engines_feat = '48e94e73-52ad-44df-8005-8fa6225176d8'
    stages_feat = 'dc4339cc-021c-423e-acb2-ca1165f9b64e'

    assert engines_feat in list(kerbal_lpg.nodes.keys())
    assert stages_feat in list(kerbal_lpg.nodes.keys())

    engines_lower_mult = roll_up_lower_multiplicity(
        lpg=kerbal_lpg,
        feature=kerbal_lpg.nodes[engines_feat],
    )

    engines_upper_mult = roll_up_upper_multiplicity(
        lpg=kerbal_lpg,
        feature=kerbal_lpg.nodes[engines_feat],
    )

    stages_lower_mult = roll_up_lower_multiplicity(
        lpg=kerbal_lpg,
        feature=kerbal_lpg.nodes[stages_feat],
    )

    stages_upper_mult = roll_up_upper_multiplicity(
        lpg=kerbal_lpg,
        feature=kerbal_lpg.nodes[stages_feat],
    )

    assert engines_lower_mult == 0
    assert engines_upper_mult == 40

    assert stages_lower_mult == 1
    assert stages_upper_mult == 5


def test_type_multiplicity_rollup(kerbal_lpg):

    real_type = '53623375-04a7-4829-84ab-a859a218aa1a'
    liquid_engine_type = 'b5d0df54-49cc-47a8-a0fa-9b332c289d19'
    rokcet_type = '4c792c29-5fd0-4846-b4e5-800a0bc037f1'

    real_ele = kerbal_lpg.nodes[real_type]
    liquid_engine_ele = kerbal_lpg.nodes[liquid_engine_type]
    rocket_ele = kerbal_lpg.nodes[rokcet_type]

    liquid_upper = roll_up_multiplicity_for_type(
        kerbal_lpg,
        liquid_engine_ele,
        "upper"
    )

    rocket_upper = roll_up_multiplicity_for_type(
        kerbal_lpg,
        rocket_ele,
        "upper"
    )

    assert liquid_upper == 40
    assert rocket_upper == 0

def test_attribute_multiplicity_rollup(kerbal_client, kerbal_lpg):

    booster_empty_mass_att = '38a7a711-47ac-48c8-9374-c55e342d74f1'
    liquid_engine_thrust_att = '912cd6cc-4d02-400b-b6cf-f4be77474cf5'

    assert True