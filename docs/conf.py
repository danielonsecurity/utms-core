# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath("../"))

import utms

project = "UTMS (Universal Time Measurement System)"
copyright = "2024-2025, Daniel Neagaru"
author = "Daniel Neagaru"
version = utms.VERSION
release = utms.VERSION



# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
              "sphinx.ext.autodoc",
              "sphinx.ext.autosummary",
              "sphinx.ext.coverage",
              "sphinx.ext.graphviz",
              "sphinx.ext.inheritance_diagram",
              "sphinx.ext.napoleon",
              "sphinx.ext.viewcode",
              "sphinx_autodoc_typehints",
              ]

# Napoleon settings
napoleon_google_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".tox"]

autodoc_member_order = (
    "bysource"  # This displays the methods in the order they appear in the source code
)


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
