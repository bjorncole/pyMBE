from pymbe.client import SysML2Client
from pathlib import Path


def kerbal_model_loaded_client() -> SysML2Client:
    helper_client = SysML2Client()
    helper_client._load_from_file(Path(__file__).parent / "data" / "Kerbal" / "elements.json")
    return helper_client
