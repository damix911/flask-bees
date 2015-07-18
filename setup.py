from setuptools import setup
from bees import info

setup(
    name = "Flask-Bees",
    version = info.version,
    packages = ["bees"],
    package_data = {
        "bees"
    },
)