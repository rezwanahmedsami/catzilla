# PyPI Publishing Setup Guide

This guide explains how to set up automated PyPI publishing for Catzilla with production-grade security and reliability.

## 🎯 Publishing Strategy

Catzilla uses a **conditional publishing strategy** that follows industry best practices:

### ✅ **Stable Releases → PyPI**
```bash
v0.1.0    # ✅ Published to PyPI (semantic version)
v1.0.0    # ✅ Published to PyPI
v2.1.5    # ✅ Published to PyPI
```

### ❌ **Pre-releases → GitHub Only**
```bash
v0.1.0-alpha1    # ❌ GitHub release only (not PyPI)
v0.1.0-beta2     # ❌ GitHub release only
v0.1.0-rc1       # ❌ GitHub release only
v0.1.0-dev       # ❌ GitHub release only
v1.0.0-test      # ❌ GitHub release only
```

This approach ensures:
- **Stable PyPI index** - Only production-ready versions
- **Safe testing** - Pre-releases don't pollute public index
- **User protection** - No accidental installation of dev versions

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
   Environment name: pypi
   ```

#### 3.2 Create GitHub Environment

1. **Go to repository settings**: https://github.com/rezwanahmedsami/catzilla/settings
2. **Navigate to**: "Environments"
3. **Create environment**: `pypi`
4. **Optional**: Add protection rules (require reviewers)

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
    user: __token__
    password: ${{ secrets.PYPI_API_TOKEN }}
    packages-dir: dist/
    verbose: true
```

## 🚀 Release Workflow

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

The workflow uses this robust pattern matching:

```yaml
# Stable version pattern: v1.2.3 (exactly)
if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v') && !contains(github.ref_name, '-')
```

**Examples:**
- `v0.1.0` → ✅ Matches (stable)
- `v1.2.3` → ✅ Matches (stable)
- `v0.1.0-alpha` → ❌ No match (pre-release)
- `v1.2.3-rc1` → ❌ No match (pre-release)

## 📊 Workflow Features

### 🛡️ **Security Features**
- **Trusted publishing** - No API tokens in secrets
- **Environment protection** - Optional manual approval
- **Permission isolation** - Minimal required permissions
- **Artifact validation** - Integrity checks before upload

### ⚡ **Quality Assurance**
- **15 test combinations** - All OS/Python combinations
- **Wheel validation** - Installation testing on all platforms
- **Functionality verification** - Import and basic functionality tests
- **Distribution integrity** - File count and format validation

### 📈 **Production Features**
- **Conditional publishing** - Smart stable/pre-release detection
- **Comprehensive logging** - Detailed workflow output
- **Post-release verification** - PyPI availability checking
- **Release summaries** - Clear success/failure reporting

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
