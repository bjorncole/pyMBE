from pymbe.client import SysML2Client


def test_all_downloaded():
    """
    Test that all elements in a given project actually downloaded
    :return: test result
    """
    # hardcode to try out while waiting to learn how fixtures work
    # values here correspond to the Part Usage Unit Test model
    api_url = 'http://sysml2-sst.intercax.com'
    project_id = 'a4f6a618-e4eb-4ac8-84b8-d6bcd3badcec'
    commit_id = 'c48aea9b-42fb-49b3-9a3e-9c39385408d7'

    client_object = SysML2Client()
    client_object.host_url = api_url
    client_object.selected_project = project_id
    client_object.selected_commit = commit_id

    client_object._download_elements()

    # Number should match the status when model committed to server - I think
    assert len(client_object.elements_by_id) == 389