# SPDX-License-Identifier: BSD-2-Clause

# Copyright (C) 2026 embedded brains GmbH & Co. KG

# This is a configuration file for the Sphinx documentation builder.

# Project information

project = "specitems"
copyright = "2020, 2026 embedded brains GmbH & Co. KG"
author = "The specitems Authors"
release = "1.0.0"

# General configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = []

autodoc_typehints = "description"

napoleon_google_docstring = True

# Options for HTML output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
