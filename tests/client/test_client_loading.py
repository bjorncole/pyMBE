from tests.conftest import (
    all_kerbal_names,
    kerbal_client,
    kerbal_ids_by_type,
)


def test_client_load_kerbal(kerbal_client):
    assert len(kerbal_client.model.elements) == 389


def test_client_load_find_names(all_kerbal_names):
    assert "Liquid Stage" in all_kerbal_names
    assert "$result" in all_kerbal_names
    assert "Empty Mass" in all_kerbal_names


def test_client_load_find_types(kerbal_ids_by_type):
    assert "PartDefinition" in kerbal_ids_by_type
    assert "FeatureTyping" in kerbal_ids_by_type
    assert "FeatureReferenceExpression" in kerbal_ids_by_type

    assert len(kerbal_ids_by_type["PartDefinition"]) == 17
