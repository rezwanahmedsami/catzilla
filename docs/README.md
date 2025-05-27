# Catzilla Documentation

This directory contains the complete documentation for the Catzilla web framework.

## Documentation Structure

- **`index.rst`** - Main documentation homepage with framework overview
- **`quickstart.rst`** - Complete getting started guide with examples
- **`advanced.rst`** - Advanced usage patterns and deployment strategies
- **`conf.py`** - Sphinx configuration for documentation generation
- **`build_docs.py`** - Helper script for building and serving documentation
- **`_static/logo.png`** - Catzilla logo (automatically copied from root during build)

## Additional Documentation Files

- **`../SYSTEM_COMPATIBILITY.md`** - Comprehensive platform and system compatibility guide
- **`../VERSION_MANAGEMENT.md`** - Version management and release workflow documentation
- **`performance-benchmarks.md`** - Detailed performance analysis and benchmarking results
- **`c-accelerated-routing.md`** - Technical deep-dive into the C routing implementation

## Building the Documentation

### Prerequisites

Make sure you have the required dependencies installed:

```bash
# Install all development dependencies (includes Sphinx documentation tools)
pip install -r requirements-dev.txt
```

This installs:
- `sphinx>=7.0.0` - Documentation generator
- `sphinx-rtd-theme>=2.0.0` - Read the Docs theme
- `myst-parser>=2.0.0` - Markdown support for Sphinx

### Build Methods

#### Method 1: Using the helper script (recommended)

```bash
# Build documentation
python build_docs.py build

# Build and serve documentation on localhost:8080
python build_docs.py build-serve

# Just serve existing documentation
python build_docs.py serve
```

#### Method 2: Using Sphinx directly

```bash
# Change to docs directory
cd docs

# Build HTML documentation
sphinx-build -b html . _build/html

# View the documentation
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
start _build\html\index.html  # Windows
```

### Output

The built documentation will be available in `_build/html/index.html`.

### Method 3: Using Make (if available)

```bash
# Build HTML documentation
make html

# Clean build files
make clean
```

## Automatic Deployment

### GitHub Pages

The documentation is automatically built and deployed using GitHub Actions:

- **Workflow**: `.github/workflows/docs.yml`
- **Trigger**: Changes to `docs/**` or `python/catzilla/**` on main branch
- **Output**: Available at `https://[username].github.io/catzilla/`

The workflow:
1. Builds the Catzilla extension (required for imports)
2. Generates documentation using Sphinx
3. Deploys to GitHub Pages automatically

### Local Testing

Before pushing documentation changes, test locally:

```bash
# Clean previous builds
python build_docs.py clean

# Build fresh documentation
python build_docs.py build

# Serve locally for review
python build_docs.py serve
```

## Documentation Features

### Comprehensive Coverage
- **Quick Start Guide**: Step-by-step installation and Hello World
- **Decorator Routing**: Complete examples of HTTP method decorators
- **Dynamic Routes**: Path parameters and variable routing
- **Request/Response**: Handling JSON, forms, headers, and cookies
- **Router Groups**: Organizing routes with prefixes and middleware
- **Error Handling**: Production-ready error management
- **CLI Deployment**: Command-line server deployment
- **Performance**: Optimization tips and benchmarking

### Professional Structure
- Modern Sphinx theme with responsive design
- Integrated Catzilla logo branding
- Cross-references and internal linking
- Code syntax highlighting
- Searchable content
- Mobile-friendly navigation

### Real-World Examples
- Complete REST API implementations
- Production deployment strategies
- Performance optimization techniques
- Error handling best practices

## Documentation Guidelines

### File Organization
- **`.rst` files**: RestructuredText for main documentation pages
- **`.md` files**: Markdown for additional content (auto-converted)
- **`_static/`**: Static assets (CSS, images, etc.)
- **`_build/`**: Generated output (ignored in git)

### Writing Style
- Clear, concise explanations
- Practical code examples
- Step-by-step instructions
- Professional tone suitable for developers

### Code Examples
- All examples are tested and functional
- Follow Python best practices
- Include both basic and advanced patterns
- Demonstrate real-world usage

## Contributing to Documentation

### Adding New Content
1. Create new `.rst` or `.md` files
2. Add references to `index.rst` toctree
3. Follow existing style and structure
4. Include practical code examples
5. Test documentation builds locally

### Editing Existing Content
1. Update the relevant `.rst` or `.md` files
2. Maintain consistent formatting
3. Ensure code examples remain functional
4. Test changes with `python build_docs.py build`

### Style Guidelines
- Use clear headings and sections
- Include code examples for all features
- Add cross-references where appropriate
- Keep explanations developer-focused

## Deployment

### Local Development
Use the provided build script for local development and testing.

### CI/CD Integration
The documentation can be built automatically in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Build Documentation
  run: |
    pip install -r requirements-dev.txt
    cd docs
    sphinx-build -b html . _build/html
```

### Hosting
The generated HTML can be hosted on:
- GitHub Pages
- Read the Docs
- Netlify
- Any static hosting service

## Support

For documentation issues or suggestions:
1. Check existing documentation structure
2. Review code examples in `/examples/` directory
3. Test with the latest Catzilla version
4. Submit issues with specific sections and improvements needed

---

This documentation provides comprehensive coverage of the Catzilla framework, from basic usage to advanced deployment strategies, suitable for developers installing via `pip install catzilla`.
