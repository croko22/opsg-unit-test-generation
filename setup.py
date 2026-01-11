#!/usr/bin/env python3
"""
Legacy setup.py for backward compatibility.
For modern installs, use: pip install -e .
"""

from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        packages=find_packages(where="src"),
        package_dir={"": "src"},
    )
