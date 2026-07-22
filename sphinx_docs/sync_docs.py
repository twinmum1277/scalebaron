#!/usr/bin/env python3
"""Copy docs_src/ into sphinx_docs/_synced/ and rewrite out-of-tree links for GitHub Pages."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_SRC = REPO_ROOT / "docs_src"
SYNCED = Path(__file__).resolve().parent / "_synced"
GITHUB = "https://github.com/twinmum1277/scalebaron/blob/main"
GITHUB_TREE = "https://github.com/twinmum1277/scalebaron/tree/main"

# (pattern, replacement) applied to synced Markdown only
LINK_REWRITES = [
    (r"\]\(\.\./INSTALL_WINDOWS_DEV\.md\)", f"]({GITHUB}/INSTALL_WINDOWS_DEV.md)"),
    (r"\]\(\.\./INSTALL_MAC_DEV\.md\)", f"]({GITHUB}/INSTALL_MAC_DEV.md)"),
    (r"\]\(\.\./README\.md\)", f"]({GITHUB}/README.md)"),
    (r"\]\(\.\./citation\.cff\)", f"]({GITHUB}/citation.cff)"),
    (r"\]\(\.\./test/testdata/csv/README\.md\)", f"]({GITHUB}/test/testdata/csv/README.md)"),
    (r"\]\(\.\./test/testdata/csv/\)", f"]({GITHUB_TREE}/test/testdata/csv)"),
    (r"\]\(\.\./test/testdata/\)", f"]({GITHUB_TREE}/test/testdata)"),
    (r"\]\(\.\./JAAS%20submission/Output%20examples/\)", f"]({GITHUB_TREE}/JAAS%20submission/Output%20examples)"),
    (r"\]\(\.\./JAAS%20submission/\)", f"]({GITHUB_TREE}/JAAS%20submission)"),
]


def main() -> None:
    if SYNCED.exists():
        for child in SYNCED.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        SYNCED.mkdir(parents=True)

    for path in DOCS_SRC.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        for pattern, repl in LINK_REWRITES:
            text = re.sub(pattern, repl, text)
        # Intra-doc links stay as foo.md; Sphinx/MyST resolves them within _synced/
        (SYNCED / path.name).write_text(text, encoding="utf-8")

    images_src = DOCS_SRC / "images"
    if images_src.is_dir():
        shutil.copytree(images_src, SYNCED / "images")

    print(f"Synced {DOCS_SRC} -> {SYNCED}")


if __name__ == "__main__":
    main()
