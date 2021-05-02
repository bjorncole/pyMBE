from pathlib import Path

import json
import pytest


@pytest.fixture
def kerbal_elements():
    return load_json_fixture("Kerbal")


def load_json_fixture(name: str) -> dict:
    here = Path(__file__)
    return json.loads((here /"fixtures" / f"{name}.json").read_text())
