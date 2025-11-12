"""
Setup script for llm-one-api

This file is kept for backward compatibility.
Please use pyproject.toml for configuration.
"""

from setuptools import setup, find_packages

setup(
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
)

