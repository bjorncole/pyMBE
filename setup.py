""" look in setup.cfg """
# pylint: disable=invalid-name
import re

from pathlib import Path


HERE = Path(__file__).parent
VERSION = HERE / "src" / "pymbe" / "_version.py"


__version__ = re.search(
    r"^__version__ = ['\"]([^'\"]*)['\"]",
    VERSION.read_text(),
    re.M,
).group(1)

__import__("setuptools").setup(version=__version__)
