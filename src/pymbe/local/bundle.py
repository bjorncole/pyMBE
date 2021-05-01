from ..client import SysML2Client
import os
import json

def download_to_local(
    host_url: str = "http://sysml2-sst.intercax.com",
    project_id: str = "Test",
    commit_id: str = "",
    download_root: str = ""
):

    grabber = SysML2Client()
    grabber.host_url = host_url
    grabber.selected_project = project_id
    grabber.selected_commit = commit_id

    grabber._download_elements()

    os.mkdir(download_root + "/" + project_id)

    for ele, data in grabber.elements_by_id.items():
        data_file = open(download_root + "/" + project_id + "/" + ele + ".json", "w")
        data_file.write(json.dumps(data, indent=4, sort_keys=False))
        data_file.close()