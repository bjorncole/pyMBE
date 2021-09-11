import pytest
import requests

from pymbe.client import APIClient

SYSML_SERVER_URL = "http://sysml2-sst.intercax.com"  # Alternative: sysml2.intercax.com


def can_connect(host: str, port: int = 9000):
    try:
        requests.get(f"{host}:{port}")
        return True
    except:
        return False


def test_client_load_kerbal(kerbal_model):
    assert len(kerbal_model.elements) == 380


def test_client_load_find_names(all_kerbal_names):
    assert "Liquid Stage" in all_kerbal_names
    assert "$result" in all_kerbal_names
    assert "Empty Mass" in all_kerbal_names


def test_client_load_find_types(kerbal_ids_by_type):
    assert "PartDefinition" in kerbal_ids_by_type
    assert "FeatureTyping" in kerbal_ids_by_type
    assert "FeatureReferenceExpression" in kerbal_ids_by_type

    assert len(kerbal_ids_by_type["PartDefinition"]) == 17


@pytest.mark.skipif(
    not can_connect(host=SYSML_SERVER_URL),
    reason=f"Can't connect to {SYSML_SERVER_URL}",
)
def test_remote_connection():
    client = APIClient()
    client.host_url = SYSML_SERVER_URL

    assert client.projects

    client.page_size = 20

    client.selected_project = list(client.projects)[0]
    client.selected_commit = list(client._get_project_commits())[0]
    model = client.get_model()

    assert model.elements
