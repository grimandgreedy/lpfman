#!/bin/python
# -*- coding: utf-8 -*-
"""
setup.py

Author: GrimAndGreedy
Created: 2025-09-07
License: MIT
"""

import setuptools


with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "lpfman",
    version = "0.1.0.3",
    author = "Grim",
    author_email = "grimandgreedy@protonmail.com",
    description = "lpfman is a TUI file manager with extensive column support.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/grimandgreedy/lpfman",
    project_urls = {
        "Bug Tracker": "https://github.com/grimandgreedy/lpfman/issues",
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
    ],
    package_dir = {"": "src"},
    packages = setuptools.find_packages(where="src"),
    python_requires = ">=3.9",

    entry_points={
        'console_scripts': [
            'lpfman = lpfman:main',
        ]
    },
    install_requires = [
        "toml",
        "pdf2image",
        "listpick >= 0.1.16.1",
    ],
)
