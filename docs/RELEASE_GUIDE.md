# 🚀 Catzilla Release Quick Reference

This guide provides quick access to Catzilla's professional release workflows.

## 📋 Release Decision Matrix

| Scenario | Command | Description |
|----------|---------|-------------|
| **Major Release** | `./scripts/bump_version.sh 1.0.0` | Full testing + comprehensive validation |
| **Minor Release** | `./scripts/bump_version.sh 0.2.0` | New features, full workflow |
| **Patch Release** | `./scripts/bump_version.sh 0.1.1` | Bug fixes, comprehensive testing |
| **Pre-release** | `./scripts/bump_version.sh 0.2.0-beta` | Testing releases, safe validation |
| **Emergency Hotfix** | `python scripts/release.py 0.1.1-hotfix` | Critical fixes, immediate deployment |
| **Quick Patch** | `python scripts/release.py 0.1.2` | Fast patch when tests already pass |

### 🎯 Professional Version Handling

Both scripts use professional version handling:

- **Git Tag**: Full version (e.g., `v0.1.0-beta`, `v0.1.0`)
- **Project Files**: Base version only (e.g., `0.1.0` from `v0.1.0-beta`)
- **CMake**: Numeric format (e.g., `0.1.0`)

**Example:**
```bash
# Input: 0.1.0-beta
# ✅ Git tag: v0.1.0-beta
# ✅ pyproject.toml: version = "0.1.0"
# ✅ __init__.py: __version__ = "0.1.0"
# ✅ CMakeLists.txt: VERSION 0.1.0
```

This ensures clean package versions while maintaining proper release tracking.

## ⚡ Quick Commands

### 🏗️ Comprehensive Release (Recommended)
```bash
# Full development workflow with comprehensive testing
./scripts/bump_version.sh 0.2.0
git push origin main && git push origin v0.2.0
```

### ⚡ Emergency Release
```bash
# Quick hotfix when speed matters
python scripts/release.py 0.1.1-emergency
```

### 🧪 Pre-release Testing
```bash
# Safe testing release (won't publish to PyPI)
./scripts/bump_version.sh 0.2.0-rc1
git push origin main && git push origin v0.2.0-rc1
```

## 🔍 Preview Changes (Dry Run)
```bash
# See what would happen without making changes
./scripts/bump_version.sh 0.2.0 --dry-run
python scripts/release.py 0.2.0 --dry-run
```

## 🚨 Troubleshooting

### "Tag already exists" Error
```bash
# Check existing tags
git tag -l

# Delete local and remote tag (if safe)
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0
```

### Version Mismatch
```bash
# Force update version file
python scripts/release.py 0.2.0 --update-version
```

## 📦 PyPI Publishing Logic

- **Stable versions** (`v1.2.3`) → Published to PyPI + GitHub
- **Pre-releases** (`v1.2.3-alpha`) → GitHub only (not PyPI)

## 🔗 Monitoring Releases

After creating a release, monitor:
- **GitHub Actions**: https://github.com/rezwanahmedsami/catzilla/actions
- **PyPI Package**: https://pypi.org/project/catzilla/
- **GitHub Releases**: https://github.com/rezwanahmedsami/catzilla/releases

---

## 📚 Full Documentation

For complete details, see [CONTRIBUTING.md](CONTRIBUTING.md#-release-process).
