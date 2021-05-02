from pymbe.client import SysML2Client
import os

def kerbal_model_loaded_client() -> SysML2Client:
    helper_client = SysML2Client()

    helper_client._load_disk_elements(str(os.getcwd()) + "\\tests\\data\\Kerbal\\elements.json")

    return helper_client
