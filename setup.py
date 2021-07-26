""" look in setup.cfg """
# pylint: disable=invalid-name
import re
from pathlib import Path

HERE = Path(__file__).parent
VERSION_FILE = HERE / "src/pymbe/_version.py"


__version__ = re.search(
    pattern=r"""^__version__\s*=\s*['"]([^'"]*)['"]""",
    string=VERSION_FILE.read_text(),
    flags=re.M,
).group(1)

__import__("setuptools").setup(version=__version__)
