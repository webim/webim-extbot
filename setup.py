import re
from pathlib import Path

import setuptools


def get_version():
    init_path = Path(__file__).parent / "src" / "extbot" / "__init__.py"
    init_contents = init_path.read_text()

    match = re.search('^__version__ = "([^"]*)"$', init_contents, re.M)
    if match is None:
        raise RuntimeError(f"No __version__ found in {init_path}")

    return match.group(1)


setuptools.setup(
    name="extbot",
    version=get_version(),
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "extbot=extbot.server:main",
        ],
    },
    install_requires=[
        "aiohttp ~= 3.8",
        "validators ~= 0.20.0",
    ],
    extras_require={
        "dev": [
            "black ~= 22.12",
            "ruff == 0.0.215",
        ],
    },
)
