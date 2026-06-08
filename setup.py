# setup.py
from setuptools import setup, find_packages

setup(
    name="sql_safe_project",
    version="0.0.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
)
