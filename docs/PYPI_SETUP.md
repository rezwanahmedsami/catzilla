# PyPI Publishing Setup Guide

This guide explains how to set up automated PyPI publishing for Catzilla with **production-grade security and reliability**.

## 🚀 **PRODUCTION-SAFE RELEASE STRATEGY**

Catzilla implements a **conditional publishing strategy** that follows industry best practices:

### ✅ **Stable Releases → Production PyPI**
```bash
v0.1.0    # ✅ Published to PyPI (pure semantic version)
v1.0.0    # ✅ Published to PyPI (pure semantic version)
v2.1.5    # ✅ Published to PyPI (pure semantic version)
```

### 🔒 **Pre-releases → GitHub Releases Only**
```bash
v0.1.0-alpha1    # 🔒 GitHub release only (NOT published to PyPI)
v0.1.0-beta2     # 🔒 GitHub release only (NOT published to PyPI)
v0.1.0-rc1       # 🔒 GitHub release only (NOT published to PyPI)
v0.1.0-dev       # 🔒 GitHub release only (NOT published to PyPI)
v1.0.0-test      # 🔒 GitHub release only (NOT published to PyPI)
```

### 🛡️ **Production Safety Features:**
- **PyPI pollution prevention** - Pre-releases never reach production index
- **User protection** - No accidental installation of dev/test versions
- **Quality assurance** - Only thoroughly tested stable versions on PyPI
- **Release testing** - Pre-releases allow safe testing via GitHub releases

## 🔧 Setup Instructions

### 1. Create PyPI Account

1. **Register at PyPI**: https://pypi.org/account/register/
2. **Verify email address**
3. **Enable 2FA** (required for publishing)

### 2. Create PyPI Project

1. **Login to PyPI**
2. **Navigate to**: https://pypi.org/manage/projects/
3. **Create new project**: "catzilla"
4. **Set project description** and basic metadata

### 3. Set Up Trusted Publishing (Recommended)

**Trusted Publishing** eliminates the need for API tokens and is more secure.

#### 3.1 Configure on PyPI

1. **Go to project settings**: https://pypi.org/manage/project/catzilla/settings/
2. **Navigate to**: "Publishing" → "Trusted Publishers"
3. **Add GitHub publisher** with these settings:
   ```
   Repository owner: rezwanahmedsami
   Repository name: catzilla
   Workflow name: release.yml
   Environment name: (leave empty - no environment used)
   ```

#### 3.2 GitHub Repository Settings

**No additional GitHub environment setup required** - the current workflow uses OIDC trusted publishing without environment restrictions for maximum security and simplicity.

### 4. Alternative: API Token Method

If you prefer API tokens over trusted publishing:

#### 4.1 Generate PyPI Token

1. **Account settings**: https://pypi.org/manage/account/token/
2. **Create token** with scope: "Entire account" or "Project: catzilla"
3. **Copy the token** (starts with `pypi-`)

#### 4.2 Add to GitHub Secrets

1. **Repository settings**: https://github.com/rezwanahmedsami/catzilla/settings/secrets/actions
2. **Add secret**: `PYPI_API_TOKEN`
3. **Paste the token**

#### 4.3 Update Workflow

If using API tokens, modify the publish step in `release.yml`:

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    packages-dir: pypi-assets/  # Updated to match current workflow
    verify-metadata: true
    skip-existing: false
    verbose: true
    # No API token needed - uses OIDC trusted publisher
```

## 🚀 Release Workflow

### 📦 **Current Release Status**

**v0.0.1 Released** ✅
- **GitHub Release**: Created with comprehensive release notes and multi-platform wheels
- **PyPI Status**: Should be published automatically (check workflow logs)
- **Verification**: Run `pip install catzilla==0.0.1` to test

### Creating a Stable Release

```bash
# 1. Ensure all changes are committed
git add .
git commit -m "Prepare v0.2.0 release"
git push

# 2. Create and push tag (triggers release)
git tag v0.2.0
git push origin v0.2.0

# 3. Workflow automatically:
#    ✅ Runs comprehensive tests (15 combinations)
#    ✅ Builds wheels for all platforms
#    ✅ Creates GitHub release
#    ✅ Publishes to PyPI (stable version detected)
#    ✅ Verifies PyPI publication
```

### Creating a Pre-release

```bash
# 1. Create pre-release tag
git tag v0.2.0-beta1
git push origin v0.2.0-beta1

# 2. Workflow automatically:
#    ✅ Runs comprehensive tests
#    ✅ Builds wheels for all platforms
#    ✅ Creates GitHub release (marked as pre-release)
#    ⏭️ Skips PyPI publication (pre-release detected)
```

## 🔍 Version Detection Logic

The workflow uses **production-safe pattern matching**:

```yaml
# PRODUCTION SAFETY: Only pure semantic versions (vX.Y.Z) - no pre-release suffixes
if: startsWith(github.ref, 'refs/tags/v') && !contains(github.ref, '-')
```

**Examples:**
- `v0.1.0` → ✅ **Publishes to PyPI** (pure semantic version)
- `v1.2.3` → ✅ **Publishes to PyPI** (pure semantic version)
- `v0.1.0-alpha` → 🔒 **GitHub release only** (contains hyphen)
- `v1.2.3-rc1` → 🔒 **GitHub release only** (contains hyphen)
- `v2.0.0-beta` → 🔒 **GitHub release only** (contains hyphen)

## 📊 Workflow Features

### 🛡️ **Security Features**
- **OIDC Trusted Publishing** - No API tokens stored in secrets
- **Production-safe conditions** - Bulletproof version detection
- **Minimal permissions** - Only `id-token: write` and `contents: write`
- **Artifact validation** - Comprehensive integrity checks before upload

### ⚡ **Quality Assurance**
- **15 test combinations** - All OS/Python version combinations (3×5 matrix)
- **Multi-platform wheel building** - Linux, macOS, Windows with cibuildwheel
- **Installation validation** - Platform-specific wheel testing
- **Functionality verification** - Import and basic functionality tests
- **Distribution integrity** - File count and format validation

### 📈 **Production Features**
- **Conditional publishing** - Smart stable/pre-release detection
- **Comprehensive logging** - Detailed workflow output for debugging
- **GitHub releases** - All versions get GitHub releases with assets
- **Professional wheel naming** - Proper platform tags (cp311-cp311-linux_x86_64, etc.)

## 🔗 Helpful Links

- **PyPI Project**: https://pypi.org/project/catzilla/
- **Trusted Publishing Guide**: https://docs.pypi.org/trusted-publishers/
- **GitHub Actions PyPI**: https://github.com/pypa/gh-action-pypi-publish
- **Semantic Versioning**: https://semver.org/

## 🆘 Troubleshooting

### Publication Failed

1. **Check workflow logs** in GitHub Actions
2. **Verify PyPI project exists** and permissions are correct
3. **Confirm trusted publishing** is configured properly
4. **Check version conflicts** - version may already exist on PyPI

### Environment Issues

1. **Verify environment name** matches in PyPI and GitHub
2. **Check protection rules** - may require manual approval
3. **Confirm workflow name** matches in trusted publisher settings

### Version Pattern Issues

1. **Use semantic versioning** - `v1.2.3` format
2. **Avoid underscores** - use hyphens for pre-releases
3. **Test with pre-release** first - `v1.2.3-test`

## 📝 Best Practices

1. **Always test pre-releases** before stable releases
2. **Use semantic versioning** consistently
3. **Monitor PyPI publication** success in workflow logs
4. **Keep backup API token** for emergency manual uploads
5. **Document breaking changes** in release notes
6. **Test installation** after PyPI publication

---

**This setup provides enterprise-grade PyPI publishing with security, reliability, and automation! 🚀**
