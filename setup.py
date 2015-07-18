from setuptools import setup
from bees import info

setup(
    name = "Flask-Bees",
    version = info.version,
    install_requires = [
        "Flask>=0.10.1",
        "Jinja2>=2.7.3",
    ],
    packages = ["bees"],
    package_data = {
        "bees": ["resources/*.html"]
    },
)