# Catzilla v0.2.0 Documentation Makefile

# Configuration
SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR    = .
BUILDDIR     = _build
PORT         ?= 8080

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help: ## Show this help message
	@echo "📚 Catzilla v0.2.0 Documentation"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \\033[36m%-15s\\033[0m %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: check
check: ## Check if dependencies are installed
	@python build_docs.py check

.PHONY: clean
clean: ## Clean build directory
	@echo "🧹 Cleaning build directory..."
	@rm -rf $(BUILDDIR)/*
	@echo "✅ Build directory cleaned"

.PHONY: html
html: check ## Build HTML documentation
	@echo "📚 Building HTML documentation..."
	@$(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo "✅ HTML documentation built successfully!"
	@echo "📂 Output: $(BUILDDIR)/html/"
	@echo "🌐 Open: file://$(shell pwd)/$(BUILDDIR)/html/index.html"

.PHONY: build
build: html ## Alias for html target

.PHONY: serve
serve: quick-build ## Build and serve documentation locally
	@echo "🌐 Serving documentation on http://localhost:$(PORT)"
	@echo "📖 Press Ctrl+C to stop the server"
	@cd $(BUILDDIR)/html && python -m http.server $(PORT)

.PHONY: watch
watch: ## Build docs and watch for changes (requires sphinx-autobuild)
	@echo "👀 Watching for changes..."
	@pip install sphinx-autobuild 2>/dev/null || true
	@sphinx-autobuild $(SOURCEDIR) $(BUILDDIR)/html --port $(PORT) --open-browser

.PHONY: linkcheck
linkcheck: ## Check for broken links
	@echo "🔗 Checking for broken links..."
	@$(SPHINXBUILD) -b linkcheck $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/linkcheck

.PHONY: pdf
pdf: ## Build PDF documentation (requires LaTeX)
	@echo "📄 Building PDF documentation..."
	@$(SPHINXBUILD) -b latex $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/latex
	@cd $(BUILDDIR)/latex && make all-pdf
	@echo "✅ PDF built: $(BUILDDIR)/latex/catzilla.pdf"

.PHONY: install-deps
install-deps: ## Install documentation dependencies
	@echo "📦 Installing documentation dependencies..."
	@pip install -r requirements-docs.txt || pip install sphinx sphinx_rtd_theme myst-parser sphinx-sitemap sphinx-copybutton

.PHONY: requirements
requirements: ## Generate requirements-docs.txt
	@echo "📝 Generating requirements-docs.txt..."
	@echo "# Catzilla v0.2.0 Documentation Dependencies" > requirements-docs.txt
	@echo "sphinx>=7.0.0" >> requirements-docs.txt
	@echo "sphinx-rtd-theme>=2.0.0" >> requirements-docs.txt
	@echo "myst-parser>=2.0.0" >> requirements-docs.txt
	@echo "sphinx-sitemap>=2.5.0" >> requirements-docs.txt
	@echo "sphinx-copybutton>=0.5.0" >> requirements-docs.txt
	@echo "sphinx-autobuild>=2021.3.14" >> requirements-docs.txt
	@echo "✅ requirements-docs.txt generated"

.PHONY: full-build
full-build: clean install-deps html linkcheck ## Clean, install deps, build, and check links

.PHONY: deploy-check
deploy-check: full-build ## Comprehensive build check for deployment
	@echo "🚀 Running deployment checks..."
	@echo "✅ HTML build: OK"
	@echo "✅ Link check: OK"
	@echo "📊 Generated files:"
	@find $(BUILDDIR)/html -name "*.html" | wc -l | xargs echo "  HTML pages:"
	@find $(BUILDDIR)/html -name "*.css" | wc -l | xargs echo "  CSS files:"
	@find $(BUILDDIR)/html -name "*.js" | wc -l | xargs echo "  JS files:"
	@echo "🎉 Ready for deployment!"

# Development targets
.PHONY: dev-server
dev-server: ## Start development server with auto-reload
	@echo "🔧 Starting development server..."
	@make watch PORT=8000

.PHONY: quick-build
quick-build: ## Quick build without warnings as errors
	@echo "⚡ Quick build (warnings allowed)..."
	@$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	@echo "✅ Quick build complete"

.PHONY: strict-build
strict-build: ## Strict build with warnings as errors (for production)
	@echo "🔒 Strict build (warnings as errors)..."
	@$(SPHINXBUILD) -b html -W $(SOURCEDIR) $(BUILDDIR)/html
	@echo "✅ Strict build complete"

# Statistics targets
.PHONY: stats
stats: html ## Show documentation statistics
	@echo "📊 Documentation Statistics"
	@echo "=========================="
	@echo "HTML pages: $$(find $(BUILDDIR)/html -name '*.html' | wc -l)"
	@echo "Total size: $$(du -sh $(BUILDDIR)/html | cut -f1)"
	@echo "Images: $$(find $(BUILDDIR)/html -name '*.png' -o -name '*.jpg' -o -name '*.svg' | wc -l)"
	@echo "Index size: $$(wc -c < $(BUILDDIR)/html/index.html) bytes"

# Targets for CI/CD
.PHONY: ci-build
ci-build: clean html linkcheck ## CI/CD build target
	@echo "🤖 CI/CD build complete"

.PHONY: production-build
production-build: ## Production build with all checks
	@echo "🏭 Production build starting..."
	@make full-build
	@make stats
	@echo "🚀 Production build complete!"
