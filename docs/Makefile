# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line
SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR    = .
BUILDDIR     = _build

# Put it first so that "make" without argument is like "make help"
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Build HTML documentation
html:
	@echo "Building Catzilla documentation..."
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)
	@echo "Documentation built successfully!"
	@echo "Open: file://$(shell pwd)/$(BUILDDIR)/html/index.html"

# Clean build directory
clean:
	@echo "Cleaning build directory..."
	@rm -rf $(BUILDDIR)/*
	@echo "Build directory cleaned."

# Build and serve documentation
serve: html
	@echo "Serving documentation on http://localhost:8080"
	@echo "Press Ctrl+C to stop the server."
	@cd $(BUILDDIR)/html && python -m http.server 8080

# Quick build (same as html)
build:
	@echo "Building Catzilla documentation..."
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)
	@echo "Documentation built successfully!"
	@echo "Open: file://$(shell pwd)/$(BUILDDIR)/html/index.html"

.PHONY: help Makefile html clean serve build
