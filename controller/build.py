# -*- coding: utf-8 -*-
"""Replaces setup.py.

From https://blagovdaryu.hashnode.dev/tremendously-speed-up-python-code-with-cython-and-package-it-with-poetry#heading-how-to-use-cython-with-poetry
"""
import os
import shutil

from Cython.Build import build_ext
from Cython.Build import cythonize
import numpy
from setuptools import Distribution
from setuptools import Extension

extensions = [
    Extension(
        "controller.utils.data_parsing_cy",
        [
            os.path.join("src", "controller", "utils", "data_parsing_cy.pyx"),
            os.path.join("src", "controller", "zlib", "crc32.c"),
        ],
    )
]

# Tanner (2/24/22): cythonizing data_parsing_cy.pyx with kwarg annotate=True will help when optimizing the code by enabling generation of the html annotation file
ext_modules = cythonize(extensions, annotate=False)

dist = Distribution({"ext_modules": ext_modules, "include_dirs": [numpy.get_include()]})
cmd = build_ext(dist)
cmd.ensure_finalized()
cmd.run()

for output in cmd.get_outputs():
    relative_extension = os.path.relpath(output, cmd.build_lib)
    dest_path = os.path.join("src", relative_extension)
    if os.path.exists(dest_path):
        os.remove(dest_path)
    shutil.copyfile(output, dest_path)
