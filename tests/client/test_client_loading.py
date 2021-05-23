from pymbe.client import SysML2Client
import pytest
from ..data_loader import kerbal_model_loaded_client

@pytest.fixture
def kerbal_client() -> SysML2Client:

    return kerbal_model_loaded_client()

@pytest.fixture()
def all_kerbal_names(kerbal_client) -> list:

    names = []

    all_elements = kerbal_client.elements_by_id

    for ele_id, ele in all_elements.items():
        if 'name' in ele:
            names.append(ele['name'])

    return names

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


def test_client_load_kerbal(kerbal_client):

    assert len(kerbal_client.elements_by_id) == 389


def test_client_load_find_names(all_kerbal_names):

    assert 'Liquid Stage' in all_kerbal_names
    assert '$result' in all_kerbal_names
    assert "Empty Mass" in all_kerbal_names


def test_client_load_find_types(kerbal_ids_by_type):

    assert 'PartDefinition' in kerbal_ids_by_type
    assert 'FeatureTyping' in kerbal_ids_by_type
    assert "FeatureReferenceExpression" in kerbal_ids_by_type

    assert len(kerbal_ids_by_type['PartDefinition']) == 17
