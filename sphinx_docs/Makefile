SPHINXOPTS    ?=
# Prefer a local docs venv if present (created via: python3 -m venv .venv-docs).
SPHINXBUILD   ?= $(shell if [ -x ../.venv-docs/bin/sphinx-build ]; then echo ../.venv-docs/bin/sphinx-build; else echo sphinx-build; fi)
SOURCEDIR     = .
BUILDDIR      = ../docs

.PHONY: help sync html clean

help:
	@echo "Targets: sync, html, clean"

sync:
	python3 sync_docs.py

html: sync
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
	@rm -rf "$(BUILDDIR)/.doctrees"
	@rm -f "$(BUILDDIR)/.buildinfo"
	@touch "$(BUILDDIR)/.nojekyll"
	@echo "Built HTML in $(BUILDDIR) (with .nojekyll)"

clean:
	rm -rf "$(BUILDDIR)" _build
	find _synced -mindepth 1 ! -name '.gitkeep' -exec rm -rf {} +
