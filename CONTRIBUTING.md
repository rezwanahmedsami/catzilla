# Contributing to Catzilla

Welcome! We're excited you want to help make Catzilla — the high-performance Python web framework with C-accelerated routing — even better. This guide will get you from clone to first pull request.

## Table of Contents

- [Important Resources](#important-resources)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [How to Report a Bug](#how-to-report-a-bug)
- [How to Suggest a Feature](#how-to-suggest-a-feature)
- [Style Guide](#style-guide)
- [Testing](#testing)
- [Making a Release](#making-a-release)
- [Code of Conduct](#code-of-conduct)
- [Where to Ask for Help](#where-to-ask-for-help)

## Important Resources

| Resource | Link |
|----------|------|
| Documentation | [docs.catzilla.dev](https://docs.catzilla.dev) |
| Issue Tracker | [GitHub Issues](https://github.com/rezwanahmedsami/catzilla/issues) |
| Source Code | [GitHub](https://github.com/rezwanahmedsami/catzilla) |
| PyPI | [pypi.org/project/catzilla](https://pypi.org/project/catzilla/) |

## Getting Started

### Prerequisites

- **Python 3.8+** (3.10+ recommended)
- **CMake 3.15+**
- **Git** with submodule support
- **C Compiler**: GCC 7+ / Clang 8+ (Linux), Xcode CLT (macOS), Visual Studio 2019+ (Windows)

### Setup

> **⚠️ You MUST use a Python virtual environment.** This is non-negotiable — it prevents dependency conflicts and keeps your system Python clean.

```bash
# 1. Clone and initialize submodules
git clone https://github.com/rezwanahmedsami/catzilla.git
cd catzilla
git submodule update --init --recursive

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

# 3. Install development dependencies
pip install -r requirements-dev.txt

# 4. Build the C extension
./scripts/build.sh                # macOS/Linux
# scripts\build.bat               # Windows

# 5. Verify everything works
python -c "import catzilla; print(f'✅ Catzilla {catzilla.__version__} ready!')"
```

### Platform-Specific Notes

**macOS:** Install Xcode Command Line Tools first:
```bash
xcode-select --install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install build-essential cmake git python3-dev python3-venv
```

**Windows:** Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with the "C++ build tools" workload, and [CMake](https://cmake.org/download/).

## Development Workflow

### 1. Create a Branch

Always work in a feature branch, never directly on `main`:

```bash
git checkout -b feature/your-feature-name    # New feature
git checkout -b fix/your-bugfix              # Bug fix
git checkout -b docs/your-docs-update        # Documentation
```

Use descriptive branch names — `feature/add-middleware-support`, not `temp`.

### 2. Make Your Changes

- **C code** goes in `src/core/`
- **Python code** goes in `python/catzilla/`
- **Tests** go in `tests/c/` (C) or `tests/python/` (Python)
- Follow the [Style Guide](STYLE_GUIDE.md)

### 3. Build and Test

```bash
./scripts/build.sh
./scripts/run_tests.sh
```

### 4. Commit

We use [Conventional Commits](https://www.conventionalcommits.org/). Every commit message has three parts:

```
<type>(<scope>): <short description>

<optional body — explain what and why, not how>

<optional footer — e.g., Closes #123, BREAKING CHANGE>
```

**Types** (the `type` field is mandatory):

| Type | When to use |
|------|-------------|
| `feat` | New feature or functionality |
| `fix` | Bug fix |
| `docs` | Documentation only changes |
| `test` | Adding or updating tests |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `chore` | Build process, tooling, CI, dependencies |

**Scope** (optional but recommended): the module or area affected — `router`, `memory`, `validation`, `middleware`, `server`, `build`.

**Examples:**

```bash
# New feature with scope and body
feat(router): add middleware support for route groups

Middleware functions now execute in a chain before route handlers.
Supports both sync and async middleware with timing metrics.

Closes #123

# Bug fix
fix(memory): resolve memory leak in router trie cleanup

Recursive cleanup was skipping nodes with NULL path_segment.
Added null checks before free() calls in all cleanup paths.

# Breaking change (note the !)
feat(api)!: change get_routes() return type from list to dict

BREAKING CHANGE: get_routes() now returns {"routes": [...]} instead of [...]

# Docs only — no body needed
docs: add testing section to CONTRIBUTING.md

# Simple fix
test: cover edge case for empty path params
```

**Never** use vague messages like `"fix stuff"`, `"update"`, or `"wip"` — the commit log is documentation that your teammates (and future you) will read.

### 5. Push and Open a Pull Request

```bash
git push origin your-branch-name
```

Then open a PR at `https://github.com/rezwanahmedsami/catzilla`.

### Before Requesting Review

Run this checklist before marking a PR ready:

- [ ] `./scripts/build.sh` passes
- [ ] `./scripts/run_tests.sh` passes
- [ ] `git status` shows no unrelated changes
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] New code has tests
- [ ] Public API changes are documented
- [ ] No memory leaks (C code)

**Reviewers will check for:**
- Logic correctness and security
- Memory leaks, error handling, edge cases
- Performance impact — benchmark if in doubt
- Tests covering the new functionality

## How to Report a Bug

Found a bug? Please [open an issue](https://github.com/rezwanahmedsami/catzilla/issues/new) with:

1. **What happened** — the actual behavior
2. **What you expected** — the intended behavior
3. **Steps to reproduce** — minimal code or commands
4. **Environment** — OS, Python version, Catzilla version (`python -c "import catzilla; print(catzilla.__version__)"`)
5. **Logs or error output** — if applicable

The more detail you provide, the faster we can fix it.

## How to Suggest a Feature

Have an idea? We'd love to hear it. [Open an issue](https://github.com/rezwanahmedsami/catzilla/issues/new) and describe:

- What problem your feature solves
- How you envision it working (API examples help!)
- Any performance implications you've considered

Tag it as an enhancement. If you'd like to implement it yourself, mention that too — we'll help guide you.

## Style Guide

We maintain detailed C and Python coding standards in [STYLE_GUIDE.md](STYLE_GUIDE.md). Quick summary:

| Area | C | Python |
|------|---|--------|
| Formatting | 4 spaces, no tabs | black (line length 88) |
| Naming | `catzilla_module_action` | snake_case, PascalCase classes |
| Types | Explicit typedefs | Full type hints on public APIs |
| Error handling | Return codes + logging | Specific exceptions |
| Memory | malloc/free pairs, NULL checks | C extension for hot paths |

Automated checks run via pre-commit hooks (black, isort, flake8, mypy).

## Testing

### Running Tests

```bash
# All tests
./scripts/run_tests.sh

# Python tests only
./scripts/run_tests.sh --python

# C tests only
./scripts/run_tests.sh --c

# Single test file
python -m pytest tests/python/test_routing.py -v

# With coverage
pip install coverage pytest-cov
python -m pytest tests/python/ --cov=catzilla --cov-report=html
```

### Test Locations

| Language | Framework | Location |
|----------|-----------|----------|
| C | Unity | `tests/c/` |
| Python | pytest | `tests/python/` |

### Writing Tests

**C tests** use the Unity framework. Add new test files to `tests/c/` and register them in the appropriate `CMakeLists.txt`. Every `malloc` must be paired with a `free` — we check for memory leaks.

**Python tests** use pytest. Group related tests in classes, use fixtures for shared setup, and follow the Arrange-Act-Assert pattern.

Coverage targets: 95%+ for core functionality, 85%+ overall.

## Making a Release

> Releases are typically done by maintainers. This section is for reference.

### Which Script to Use

| Scenario | Command | Reason |
|----------|---------|--------|
| Major release (1.0.0) | `./scripts/bump_version.sh 1.0.0` | Full test suite + validation |
| Minor release (0.3.0) | `./scripts/bump_version.sh 0.3.0` | New features need full coverage |
| Patch release (0.2.1) | `./scripts/bump_version.sh 0.2.1` | Bug fixes need test coverage |
| Pre-release testing | `./scripts/bump_version.sh 0.3.0-beta` | Safe validation workflow |
| Security hotfix | `python scripts/release.py 0.2.4-hotfix` | Speed matters |
| Emergency patch | `python scripts/release.py 0.2.5` | Quick deployment |

### Publishing Rules

```
Push tag v1.0.0
    │
    ▼
┌────────────────┐    no hyphen?    ┌──────────┐
│ GitHub Actions │ ──────────────►  │ PyPI     │
│ builds wheels  │                  │ publish  │
│ runs tests     │    has hyphen?   └──────────┘
└────────────────┘ ──────────────► GitHub release only
```

- **Stable** tags (`v1.0.0`, `v0.2.1`) → PyPI + GitHub release
- **Pre-release** tags (`v1.0.0-beta`, `v0.2.0-rc1`) → GitHub release only

The hyphen in the tag controls this — the CI workflow checks `!contains(github.ref, '-')`.

### Release Checklist

1. Ensure all tests pass: `./scripts/run_tests.sh`
2. Run the appropriate version script (see table above)
3. Push: `git push origin main && git push origin v0.3.0`
4. Monitor [GitHub Actions](https://github.com/rezwanahmedsami/catzilla/actions)
5. Verify on [PyPI](https://pypi.org/project/catzilla/): `pip install catzilla==0.3.0 --no-cache-dir`

### Version Rules

- **Never** manually edit version numbers in `pyproject.toml`, `setup.py`, or `__init__.py` — use the scripts
- **Never** run both release scripts for the same version — they will conflict
- **Always** verify consistency: `python scripts/version.py --check`
- Git tags track full versions (e.g., `v0.1.0-beta`), but project files use clean semver (`0.1.0`)

## Recognition

We appreciate every contribution. When you submit a PR:

- Maintainers will review it as soon as possible
- Accepted contributions are credited in release notes
- Major contributors may be invited as collaborators

Thank you for helping make Catzilla better!

## Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/). Be respectful, constructive, and welcoming. Harassment or disrespectful behavior will not be tolerated.

## Where to Ask for Help

- **Questions?** [Open a Discussion](https://github.com/rezwanahmedsami/catzilla/discussions) or ask in an issue
- **Stuck on a contribution?** Mention `@rezwanahmedsami` in your PR or issue
- **Documentation:** [docs.catzilla.dev](https://docs.catzilla.dev)

---

Thank you for contributing to Catzilla! Every PR, bug report, and feature suggestion makes the project better.
