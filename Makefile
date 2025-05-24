# Catzilla Makefile
.PHONY: build install test benchmark clean dev-install docs

# Default Python and build settings
PYTHON := python3
BUILD_DIR := build
VENV_DIR := venv

# Build the C extension and install in development mode
build:
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
	@echo "  make build         - Build C extension in-place"
	@echo "  make install       - Install in development mode"
	@echo "  make dev-install   - Set up development environment"
	@echo "  make test          - Run all tests (C and Python)"
	@echo "  make benchmark     - Run performance benchmarks"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docs          - Show documentation info"
	@echo "  make help          - Show this help message"
	@echo ""
	@echo "Quick start:"
	@echo "  make dev-install   # Set up development environment"
	@echo "  make test          # Verify everything works"
	@echo "  make benchmark     # Run performance tests"

# Default target
all: build install test
