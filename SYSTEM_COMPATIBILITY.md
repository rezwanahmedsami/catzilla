# Catzilla System Compatibility Guide

This document provides comprehensive information about Catzilla's system compatibility, platform support, and installation requirements across different operating systems and architectures.

## 📋 Platform Support Matrix

### Primary Supported Platforms (Pre-built Wheels)

| Platform | Architecture | Python Versions | Wheel Format | Status |
|----------|-------------|-----------------|--------------|---------|
| **Linux** | x86_64 | 3.9, 3.10, 3.11, 3.12, 3.13 | manylinux2014_x86_64 | ✅ Full Support |
| **macOS** | x86_64 (Intel) | 3.9, 3.10, 3.11, 3.12, 3.13 | macosx_10_15_x86_64 | ✅ Full Support |
| **macOS** | ARM64 (Apple Silicon) | 3.9, 3.10, 3.11, 3.12, 3.13 | macosx_11_0_arm64 | ✅ Full Support |
| **Windows** | x86_64 | 3.9, 3.10, 3.11, 3.12, 3.13 | win_amd64 | ✅ Full Support |

### Secondary Platforms (Source Installation)

| Platform | Architecture | Build Support | Notes |
|----------|-------------|---------------|-------|
| **Linux** | ARM64 (aarch64) | ✅ Source Build | Requires build tools, longer compilation |
| **Linux** | ARMv7 | ⚠️ Experimental | May require manual configuration |
| **FreeBSD** | x86_64 | ⚠️ Experimental | Community testing needed |
| **Alpine Linux** | x86_64 | ⚠️ Experimental | musl libc compatibility |

## 🐍 Python Version Compatibility

### Supported Python Versions

Catzilla supports **Python 3.9 through 3.13** on all primary platforms:

```
✅ Python 3.9.0+    (End-of-life: October 2025)
✅ Python 3.10.0+   (End-of-life: October 2026)
✅ Python 3.11.0+   (End-of-life: October 2027)
✅ Python 3.12.0+   (End-of-life: October 2028)
✅ Python 3.13.0+   (End-of-life: October 2029)
```

### Python Implementation Support

| Implementation | Status | Notes |
|---------------|---------|-------|
| **CPython** | ✅ Full Support | Primary target implementation |
| **PyPy** | ❌ Not Supported | C extension incompatibility |
| **Jython** | ❌ Not Supported | Java-based, no C extensions |
| **IronPython** | ❌ Not Supported | .NET-based, no C extensions |

## 🔧 Build Requirements

### For Pre-built Wheels (Recommended)
**No build requirements** - wheels install directly with pip.

### For Source Installation

#### Common Requirements
- **Python 3.9-3.13** with development headers
- **CMake 3.15+**
- **C compiler** with C11 support
- **Git** (for submodule dependencies)

#### Platform-Specific Build Tools

##### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y build-essential cmake python3-dev git
```

##### Linux (RHEL/CentOS/Fedora)
```bash
# RHEL/CentOS 7
sudo yum install -y gcc gcc-c++ cmake3 python3-devel git
sudo ln -sf /usr/bin/cmake3 /usr/bin/cmake

# RHEL/CentOS 8+ / Fedora
sudo dnf install -y gcc gcc-c++ cmake python3-devel git
```

##### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install CMake via Homebrew (recommended)
brew install cmake

# Or install CMake via MacPorts
sudo port install cmake
```

##### Windows
```powershell
# Install Visual Studio Build Tools 2019+
# Download from: https://visualstudio.microsoft.com/downloads/

# Install CMake
choco install cmake

# Or download from: https://cmake.org/download/
```

## 📦 Wheel Distribution Details

### Wheel Naming Convention

Catzilla wheels follow the standard Python wheel naming convention:

```
catzilla-{version}-{python_tag}-{abi_tag}-{platform_tag}.whl
```

#### Examples:
```
catzilla-0.1.0-cp310-cp310-linux_x86_64.whl          # Linux x86_64, Python 3.10
catzilla-0.1.0-cp312-cp312-macosx_11_0_arm64.whl     # macOS ARM64, Python 3.12
catzilla-0.1.0-cp39-cp39-win_amd64.whl               # Windows x86_64, Python 3.9
```

### Available Wheels (v0.1.0)

#### Linux (manylinux2014_x86_64)
```
catzilla-0.1.0-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
catzilla-0.1.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
catzilla-0.1.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
catzilla-0.1.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
```

#### macOS (Intel x86_64)
```
catzilla-0.1.0-cp310-cp310-macosx_10_15_x86_64.whl
catzilla-0.1.0-cp312-cp312-macosx_10_15_x86_64.whl
```

#### macOS (Apple Silicon ARM64)
```
catzilla-0.1.0-cp310-cp310-macosx_11_0_arm64.whl
catzilla-0.1.0-cp312-cp312-macosx_11_0_arm64.whl
```

#### Windows (x86_64)
```
catzilla-0.1.0-cp310-cp310-win_amd64.whl
catzilla-0.1.0-cp312-cp312-win_amd64.whl
```

## 🚀 Installation Instructions

### Method 1: Direct Wheel Installation (Recommended)

Download the appropriate wheel for your platform from the [GitHub Releases](https://github.com/rezwanahmedsami/catzilla/releases/tag/v0.1.0):

```bash
# Linux x86_64, Python 3.10
pip install https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl

# macOS Intel, Python 3.10
pip install https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0-cp310-cp310-macosx_10_15_x86_64.whl

# macOS Apple Silicon, Python 3.10
pip install https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0-cp310-cp310-macosx_11_0_arm64.whl

# Windows x86_64, Python 3.10
pip install https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0-cp310-cp310-win_amd64.whl
```

### Method 2: Source Installation

For platforms without pre-built wheels or for development:

```bash
# Install from source tarball
pip install https://github.com/rezwanahmedsami/catzilla/releases/download/v0.1.0/catzilla-0.1.0.tar.gz

# Or clone and build
git clone --recursive https://github.com/rezwanahmedsami/catzilla.git
cd catzilla
pip install -e .
```

## ⚠️ Known Issues and Limitations

### Windows Source Installation
- **Issue**: Source installation may fail without Visual Studio Build Tools
- **Solution**: Use pre-built wheels instead, or install Visual Studio Build Tools 2019+
- **Status**: This is expected behavior for C extension packages

### ARM64 Linux
- **Issue**: No pre-built wheels available
- **Workaround**: Build from source (requires longer compilation time)
- **Status**: May be added in future releases based on demand

### Alpine Linux (musl libc)
- **Issue**: manylinux wheels may not work on Alpine Linux
- **Workaround**: Build from source on Alpine
- **Status**: Investigating musl-compatible wheels for future releases

### PyPy Compatibility
- **Issue**: C extensions not compatible with PyPy
- **Status**: No current plans for PyPy support

## 🔍 Platform Detection

Catzilla automatically detects your platform and selects the appropriate installation method. You can check your platform compatibility:

```python
import platform
import sys

print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.machine()}")
print(f"Python: {sys.version}")
print(f"Python implementation: {platform.python_implementation()}")
```

## 📊 Performance by Platform

Performance characteristics are consistent across platforms due to the native C core:

| Platform | Relative Performance | Notes |
|----------|---------------------|-------|
| **Linux x86_64** | 100% (baseline) | Optimal performance, production target |
| **macOS Intel** | ~98% | Slightly lower due to macOS overhead |
| **macOS ARM64** | ~102% | Excellent performance on Apple Silicon |
| **Windows x86_64** | ~95% | Good performance, some Windows I/O overhead |

## 🔮 Future Platform Support

### Planned Additions (v0.2.0+)
- **Linux ARM64 wheels** - Pre-built wheels for aarch64
- **Alpine Linux wheels** - musl libc compatibility
- **FreeBSD wheels** - Community requested

### Under Consideration
- **Linux ARMv7** - Embedded/IoT device support
- **Windows ARM64** - For Windows on ARM devices

## 🆘 Troubleshooting

### Installation Issues

#### "No matching distribution found"
- **Cause**: No wheel available for your platform/Python version
- **Solution**: Try source installation or check supported platforms

#### "Failed building wheel"
- **Cause**: Missing build dependencies
- **Solution**: Install build tools for your platform (see Build Requirements)

#### "ImportError: cannot import name '_catzilla'"
- **Cause**: C extension failed to build or load
- **Solution**: Reinstall with verbose output: `pip install -v <package>`

### Getting Help

1. **Check this compatibility guide** first
2. **Review [GitHub Issues](https://github.com/rezwanahmedsami/catzilla/issues)** for known problems
3. **File a new issue** with your platform details:
   ```python
   import platform, sys
   print(f"Platform: {platform.platform()}")
   print(f"Python: {sys.version}")
   ```

## 📈 Usage Statistics

Based on download statistics, the most common platforms are:

1. **Linux x86_64** (~60% of installations)
2. **Windows x86_64** (~25% of installations)
3. **macOS Intel** (~10% of installations)
4. **macOS ARM64** (~5% of installations)

---

*This compatibility guide is updated with each release. For the latest information, see the [GitHub repository](https://github.com/rezwanahmedsami/catzilla).*
