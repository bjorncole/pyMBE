from ..fixtures.data_loader import kerbal_model_loaded_client
from pymbe.graph.lpg import SysML2LabeledPropertyGraph
from pymbe.client import SysML2Client
from pymbe.interpretation.interp_playbooks import create_set_with_new_instances
import pytest

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