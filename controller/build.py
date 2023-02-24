from Cython.Build import cythonize
import os, numpy

from setuptools import Extension


def build(setup_kwargs):
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
    extensions = cythonize(extensions, annotate=False)

    setup_kwargs.update(
        {
            "ext_modules": extensions,
            "include_dirs": setup_kwargs.get("include_dirs", []) + [numpy.get_include()],
        }
    )
