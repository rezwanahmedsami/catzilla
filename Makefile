# Catzilla Makefile
.PHONY: build install test benchmark clean dev-install docs install-jemalloc

# Default Python and build settings
PYTHON := python3
BUILD_DIR := build
VENV_DIR := venv

# jemalloc configuration
JEMALLOC_VERSION = 5.3.0
JEMALLOC_PREFIX = je_
USE_JEMALLOC ?= 1

ifeq ($(USE_JEMALLOC), 1)
    export CATZILLA_USE_JEMALLOC=1
    JEMALLOC_CFLAGS = -DCATZILLA_USE_JEMALLOC=1
    JEMALLOC_LDFLAGS = -ljemalloc
endif

# Install jemalloc if needed
install-jemalloc:
	@echo "🔍 Checking for jemalloc..."
	@if [ "$(USE_JEMALLOC)" = "1" ]; then \
		if ! pkg-config --exists jemalloc 2>/dev/null; then \
			echo "📦 Installing jemalloc development package..."; \
			if command -v brew >/dev/null 2>&1; then \
				echo "🍺 Using Homebrew to install jemalloc..."; \
				brew install jemalloc; \
			elif command -v apt-get >/dev/null 2>&1; then \
				echo "📦 Using apt to install jemalloc-dev..."; \
				sudo apt-get update && sudo apt-get install -y libjemalloc-dev; \
			elif command -v yum >/dev/null 2>&1; then \
				echo "📦 Using yum to install jemalloc-devel..."; \
				sudo yum install -y jemalloc-devel; \
			elif command -v dnf >/dev/null 2>&1; then \
				echo "📦 Using dnf to install jemalloc-devel..."; \
				sudo dnf install -y jemalloc-devel; \
			else \
				echo "🔨 Building jemalloc from source..."; \
				curl -L https://github.com/jemalloc/jemalloc/releases/download/$(JEMALLOC_VERSION)/jemalloc-$(JEMALLOC_VERSION).tar.bz2 | tar xj; \
				cd jemalloc-$(JEMALLOC_VERSION) && \
				./configure --prefix=/usr/local --with-jemalloc-prefix=$(JEMALLOC_PREFIX) && \
				$(MAKE) && sudo $(MAKE) install; \
				cd .. && rm -rf jemalloc-$(JEMALLOC_VERSION); \
			fi; \
		else \
			echo "✅ jemalloc development package already installed"; \
		fi; \
	else \
		echo "⚠️  jemalloc disabled (USE_JEMALLOC=0)"; \
	fi

# Build the C extension and install in development mode
build: install-jemalloc
	@echo "🚀 Building Catzilla with jemalloc support..."
	$(PYTHON) setup.py build_ext --inplace

# Install Catzilla in development mode
install: build
	$(PYTHON) -m pip install -e .

# Create virtual environment and install dependencies
dev-install:
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install --upgrade pip
	. $(VENV_DIR)/bin/activate && pip install -e .
	. $(VENV_DIR)/bin/activate && pip install fastapi uvicorn flask django gunicorn matplotlib pandas seaborn

# Run all tests
test:
	cd tests/c && make test
	$(PYTHON) -m pytest tests/python/ -v

# Run comprehensive performance benchmarks
benchmark:
	@echo "🚀 Running Catzilla performance benchmarks..."
	@echo "This will test Catzilla against FastAPI, Flask, and Django"
	@echo "Results will be saved to benchmarks/results/"
	@./benchmarks/run_all.sh
	@echo ""
	@echo "📊 Generating performance visualizations..."
	@$(PYTHON) benchmarks/visualize_results.py
	@echo ""
	@echo "✅ Benchmark complete! Check benchmarks/results/ for detailed results"

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)
	rm -rf *.egg-info
	rm -rf dist
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -f python/catzilla/*.so

# Generate documentation
docs:
	@echo "📚 Documentation available in docs/ directory"
	@echo "Key files:"
	@echo "  - docs/getting-started.md"
	@echo "  - docs/routing.md"
	@echo "  - docs/performance.md"
	@echo "  - docs/examples.md"

# Show help
help:
	@echo "Catzilla Development Commands:"
	@echo ""
	@echo "  make build         - Build C extension with jemalloc support"
	@echo "  make install       - Install in development mode"
	@echo "  make dev-install   - Set up development environment"
	@echo "  make test          - Run all tests (C and Python)"
	@echo "  make benchmark     - Run performance benchmarks"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docs          - Show documentation info"
	@echo "  make install-jemalloc - Install jemalloc if needed"
	@echo "  make help          - Show this help message"
	@echo ""
	@echo "jemalloc Configuration:"
	@echo "  USE_JEMALLOC=1     - Enable jemalloc (default)"
	@echo "  USE_JEMALLOC=0     - Disable jemalloc (fallback to malloc)"
	@echo ""
	@echo "Quick start:"
	@echo "  make dev-install   # Set up development environment"
	@echo "  make test          # Verify everything works"
	@echo "  make benchmark     # Run performance tests"

# Default target
all: build install test
