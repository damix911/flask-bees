from setuptools import setup

version = "1.0.0"

setup(
    name = "Flask-Bees",
    version = version,
    install_requires = [
        "Flask>=0.10.1",
        "Jinja2>=2.7.3",
    ],
    packages = ["bees"],
    package_data = {
        "bees": ["resources/*.html"]
    },
)