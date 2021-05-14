from pymbe.client import SysML2Client
import os

def kerbal_model_loaded_client() -> SysML2Client:
    helper_client = SysML2Client()

    file_name = "\\tests\\data\\Kerbal\\elements.json"
    #file_name = "\\data\\Kerbal\\elements.json"

    helper_client._load_disk_elements(os.getcwd() + str(file_name))

    return helper_client
