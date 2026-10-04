"""Sphinx configuration for photon_transport_code documentation."""

import os
import sys

# Make photon_transport_code importable from docs/source/
HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -- Project information ---------------------------------------------------
project = "Photon Transport Module"
copyright = "2026, MCDC Contributors"
author = "MCDC Contributors"
release = "1.0"

# -- General configuration -------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
]

autosummary_generate = True
autosectionlabel_prefix_document = True
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_returns = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": False,
}
autodoc_member_order = "bysource"

# Mock numba so autodoc doesn't require JIT compilation
autodoc_mock_imports = ["numba"]

templates_path = []
exclude_patterns = ["_build"]

# -- HTML output -----------------------------------------------------------
html_theme = "alabaster"
html_static_path = []
