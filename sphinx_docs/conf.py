# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = "ScaleBarOn"
copyright = "BNEIR / ScaleBarOn contributors"
author = "Tracy Punshon"
release = "1.0.2"
version = "1.0.2"

extensions = [
    "myst_parser",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
myst_heading_anchors = 3

templates_path = ["_templates"]
exclude_patterns = ["_synced/.gitkeep", "Thumbs.db", ".DS_Store", "Makefile", "conf.py"]

# Keep doctrees out of the published _site/ tree.
doctreedir = "_build/doctrees"

source_suffix = {
    ".md": "markdown",
}

root_doc = "index"

html_theme = "furo"
html_title = "ScaleBarOn"
html_static_path = ["_static"]