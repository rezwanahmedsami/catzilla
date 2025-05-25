# Catzilla Version Management

This document describes how to properly manage versions for the Catzilla framework.

## 🎯 Version Management System

Catzilla uses a **single source of truth** approach for version management, ensuring consistency across all files and components.

### Version Files
- **`pyproject.toml`** - Main project version (PEP 621)
- **`setup.py`** - Build configuration version
- **`python/catzilla/__init__.py`** - Python module version
- **`CMakeLists.txt`** - C library version
- **`scripts/version.py`** - Version management script

## 🚀 Quick Version Update

### Option 1: Automated Bump (Recommended)
```bash
# Patch release (bug fixes)
./scripts/bump_version.sh 0.1.1

# Minor release (new features)
./scripts/bump_version.sh 0.2.0

# Major release (breaking changes)
./scripts/bump_version.sh 1.0.0

# Pre-release
./scripts/bump_version.sh 0.2.0-beta
```

### Option 2: Manual Update
```bash
# Update version in all files
python3 scripts/version.py 0.2.0

# Manual commit and tag
git add .
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
git push origin v0.2.0
```

## 🛠️ Version Management Tools

### `scripts/version.py`
Professional version management script with validation and consistency checking.

```bash
# Show current version status
python3 scripts/version.py

# Update to new version
python3 scripts/version.py 0.2.0

# Check version consistency
python3 scripts/version.py --check

# Show current version from script
python3 scripts/version.py --current
```

### `scripts/bump_version.sh`
Complete automated version bump with testing and validation.

```bash
# Full automated bump
./scripts/bump_version.sh 0.2.0

# Skip tests (faster)
./scripts/bump_version.sh 0.2.0 --no-tests

# Update files only (no commit)
./scripts/bump_version.sh 0.2.0 --no-commit

# Preview changes (dry run)
./scripts/bump_version.sh 0.2.0 --dry-run

# Show help
./scripts/bump_version.sh --help
```

## 📋 Semantic Versioning Strategy

Catzilla follows [Semantic Versioning 2.0.0](https://semver.org/):

### Version Format: `MAJOR.MINOR.PATCH[-PRERELEASE]`

- **MAJOR** (1.0.0) - Incompatible API changes
- **MINOR** (0.2.0) - New functionality (backwards compatible)
- **PATCH** (0.1.1) - Bug fixes (backwards compatible)
- **PRERELEASE** (0.2.0-beta) - Pre-release versions

### Examples

| Version | Type | Description |
|---------|------|-------------|
| `0.1.1` | Patch | Bug fixes, performance improvements |
| `0.2.0` | Minor | New features, middleware support |
| `1.0.0` | Major | First stable release, API stability |
| `0.2.0-beta` | Pre-release | Beta testing version |
| `1.1.0-rc1` | Release Candidate | Release candidate |

## 🔄 Release Workflow

### 1. **Prepare Release**
```bash
# Check current status
python3 scripts/version.py --check

# Run tests
./scripts/run_tests.sh
```

### 2. **Bump Version**
```bash
# Automated bump (recommended)
./scripts/bump_version.sh 0.2.0

# Or manual update
python3 scripts/version.py 0.2.0
git add .
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
```

### 3. **Release**
```bash
# Push to trigger release workflow
git push origin main
git push origin v0.2.0
```

### 4. **Verify Release**
- Check [GitHub Releases](https://github.com/rezwanahmedsami/catzilla/releases)
- Verify wheel artifacts are built
- Test installation from release

## 🔍 Version Consistency Checking

The version management system automatically validates consistency across all files:

```bash
# Check consistency
python3 scripts/version.py --check
```

**Example Output:**
```
📋 Catzilla Version Status
==================================================
✅ pyproject.toml        0.1.0
✅ setup.py              0.1.0
✅ __init__.py           0.1.0
✅ CMakeLists.txt        0.1.0

✅ All versions are consistent!
```

## 🚨 Troubleshooting

### Version Mismatch
```bash
# Fix inconsistent versions
python3 scripts/version.py 0.1.0
```

### Failed Tests During Bump
```bash
# Skip tests if needed
./scripts/bump_version.sh 0.1.1 --no-tests

# Fix tests first (recommended)
./scripts/run_tests.sh
```

### Tag Already Exists
```bash
# Delete local tag
git tag -d v0.1.0

# Delete remote tag (if needed)
git push origin :refs/tags/v0.1.0
```

## 📝 Best Practices

### ✅ Do
- Use semantic versioning
- Run tests before releasing
- Use automated bump script
- Check version consistency
- Write meaningful commit messages
- Create release notes

### ❌ Don't
- Edit version files manually
- Skip version consistency checks
- Release without testing
- Use non-semantic version numbers
- Forget to push tags

## 🎯 Integration with CI/CD

Version bumps automatically trigger:

1. **GitHub Actions Release Workflow**
   - Multi-platform wheel building
   - Automated testing
   - GitHub Release creation
   - Asset upload

2. **Documentation Updates**
   - API documentation regeneration
   - Version-specific docs

3. **Performance Benchmarks**
   - Automated performance testing
   - Benchmark result updates

## 📖 Examples

### Patch Release (Bug Fix)
```bash
# Fix a routing bug
git checkout -b fix/routing-bug
# ... make fixes ...
git commit -m "Fix routing parameter parsing"
git push origin fix/routing-bug

# After merge to main
./scripts/bump_version.sh 0.1.1
```

### Minor Release (New Feature)
```bash
# Add middleware support
git checkout -b feature/middleware
# ... implement feature ...
git commit -m "Add middleware support"
git push origin feature/middleware

# After merge to main
./scripts/bump_version.sh 0.2.0
```

### Major Release (Breaking Changes)
```bash
# API redesign
git checkout -b major/api-v2
# ... breaking changes ...
git commit -m "Redesign routing API for v2"
git push origin major/api-v2

# After merge to main
./scripts/bump_version.sh 1.0.0
```

This version management system ensures reliable, consistent, and professional release processes for Catzilla! 🚀
