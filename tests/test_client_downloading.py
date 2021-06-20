import pytest

from pymbe.client import SysML2Client


@pytest.mark.skip
def test_all_downloaded():
    """
    Test that all elements in a given project actually downloaded
    :return: test result
    """
    # hardcode to try out while waiting to learn how fixtures work
    # values here correspond to the Part Usage Unit Test model
    api_url = "http://sysml2-sst.intercax.com"

    client = SysML2Client()
    client.host_url = api_url
    assert client.projects, f"Didn't find any projects in the '{api_url}'"

    # Load a project
    a_project = list(client.projects)[0]
    client.selected_project = a_project
    commits = client._get_project_commits()
    assert commits, f"Didn't find any commits for project: {a_project}"

    a_commit = commits[0]
    client.selected_commit = a_commit

    client._download_elements()

    assert client.elements_by_id, f"Could not find elements for commit: {a_commit}"
