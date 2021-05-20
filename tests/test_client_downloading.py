from pymbe.client import SysML2Client


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
