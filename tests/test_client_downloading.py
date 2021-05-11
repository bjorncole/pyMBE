from pymbe.client import SysML2Client
from pymbe.graph import SysML2LabeledPropertyGraph
from .data_loader import kerbal_model_loaded_client


def test_all_downloaded():
    """
    Test that all elements in a given project actually downloaded
    :return: test result
    """
    # hardcode to try out while waiting to learn how fixtures work
    # values here correspond to the Part Usage Unit Test model
    api_url = 'http://sysml2-sst.intercax.com'
    project_id = 'd27e2bc7-d4a2-423e-bb04-f8a9d48393e7'
    commit_id = 'a489eed4-a93e-4ea9-a079-80fafa7cbcb5'

    client_object = SysML2Client()
    client_object.host_url = api_url
    client_object.selected_project = project_id
    client_object.selected_commit = commit_id

    client_object._download_elements()

    # Number should match the status when model committed to server - I think
    assert len(client_object.elements_by_id) == 143


def test_ele_v_relationship():
    """
    Test that elements are correctly partitioned between non-relationship and relationship
    :return: test result
    """
    # hardcode to try out while waiting to learn how fixtures work
    # values here correspond to the Part Usage Unit Test model
    api_url = 'http://sysml2-sst.intercax.com'
    project_id = 'd27e2bc7-d4a2-423e-bb04-f8a9d48393e7'
    commit_id = 'a489eed4-a93e-4ea9-a079-80fafa7cbcb5'

    client_object = SysML2Client()
    client_object.host_url = api_url
    client_object.selected_project = project_id
    client_object.selected_commit = commit_id

    client_object._download_elements()

    trial_graph = SysML2LabeledPropertyGraph()
    trial_graph.update(client_object.elements_by_id)

    assert len(trial_graph.nodes) == 66
    assert len(trial_graph.edges) == (143 - 66)


def test_ele_types():
    """
    Test that elements are downloaded with correct metatype
    :return: test result
    """
    assert True


def test_eles_populated():
    """
    Test that elements are populated with actual data
    :return: test result
    """
    assert True


def test_local_client():
    """
    Test that the local client for fixture support runs without exception
    :return: test result
    """

    pre_loaded = kerbal_model_loaded_client()

    assert pre_loaded is not None
