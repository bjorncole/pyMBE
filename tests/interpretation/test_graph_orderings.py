import pytest
import networkx as nx

from pymbe.graph.lpg import SysML2LabeledPropertyGraph
from pymbe.client import SysML2Client

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


def test_part_def_graph_ordering(kerbal_lpg):

    pdg = kerbal_lpg.get_projection("Part Definition Graph")
    rocket_part = '63f5c455-261b-4a80-9a3b-5a9bef2361da'
    flea = '68f08797-0e68-47b1-bad5-9e734af2742f'
    hammer = '628929a4-1dc2-4c34-aefb-2653faaa46fe'
    fuel_tank_section = 'b51e6a60-fdf3-401c-b267-4d3d6aeaa19d'

    for comp in nx.connected_components(pdg.to_undirected()):
        connected_sub = nx.subgraph(pdg, list(comp))
        sorted_sub = list(nx.topological_sort(connected_sub))

        if rocket_part in sorted_sub:
            assert flea in sorted_sub
            assert hammer in sorted_sub
            assert fuel_tank_section in sorted_sub

            assert sorted_sub.index(flea) > sorted_sub.index(rocket_part)
            assert sorted_sub.index(hammer) > sorted_sub.index(rocket_part)
            assert sorted_sub.index(fuel_tank_section) > sorted_sub.index(rocket_part)
