#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="openshorts",
    version="2.0.0",
    author="Tyler Hudson",
    author_email="",
    description="A professional video clipper for creating short-form content with AI-powered features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tylerhudson/openshorts",
    py_modules=["openshorts"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Content Creators",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    extras_require={
        "ai": ["ollama"],
        "dev": ["pyinstaller", "build", "twine"],
    },
    entry_points={
        "console_scripts": [
            "openshorts=openshorts:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["README.md", "requirements.txt"],
    },
)