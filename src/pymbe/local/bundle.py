import os
import json

from ..client import SysML2Client


def download_to_local(
    host_url: str = "http://sysml2-sst.intercax.com",
    project_name: str = "Name",
    project_id: str = "",
    commit_id: str = "",
    download_root: str = ""
):

    grabber = SysML2Client()
    grabber.host_url = host_url
    grabber.selected_project = project_id
    grabber.selected_commit = commit_id

    server_elements = grabber._get_elements_from_server()

    print(grabber.elements_url)

    os.mkdir(download_root + "/" + project_name)

    data_file = open(download_root + "/" + project_name + "/elements.json", "w")
    data_file.write(json.dumps(server_elements, indent=4, sort_keys=False))
    data_file.close()
