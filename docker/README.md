# Catzilla Docker Cross-Platform Testing

🐳 **Professional Docker-based cross-platform testing environment for Catzilla**

This Docker setup allows you to test Catzilla locally across multiple platforms (Linux and Windows) using the exact same environment as our CI/CD pipeline, saving time and costs.

## 🎯 Benefits

- **💰 Cost Savings**: Test locally before pushing to GitHub (saves CI minutes)
- **⚡ Faster Feedback**: Get instant results without waiting for CI
- **🔍 Better Debugging**: Interactive containers for issue investigation
- **🎯 Exact CI Replication**: Same environment as GitHub Actions
- **🚀 Parallel Testing**: Test multiple platforms simultaneously

## 🏗️ Architecture

```
docker/
├── docker-compose.yml       # Multi-platform container orchestration
├── linux/
│   ├── Dockerfile          # Ubuntu 22.04 + jemalloc
│   └── test.sh             # Linux test runner
├── windows/
│   ├── Dockerfile          # Windows Server 2022 + vcpkg
│   └── test.bat            # Windows test runner
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Setup Docker Testing Environment

```bash
# One-time setup (builds images, creates scripts)
./scripts/setup_docker_testing.sh
```

### 2. Run Tests

```bash
# Quick test (Linux only - fastest)
./scripts/run_tests.sh --docker linux

# Full cross-platform test
./scripts/run_tests.sh --docker all

# Windows only
./scripts/run_tests.sh --docker windows
```

### 3. Simulate CI Pipeline

```bash
# Simulate complete GitHub Actions CI locally
./scripts/simulate_ci.sh --full --report
```

## 📚 Available Commands

### Testing Commands

| Command | Description | Use Case |
|---------|-------------|----------|
| `./scripts/run_tests.sh --docker linux` | Test on Linux | Quick feedback |
| `./scripts/run_tests.sh --docker windows` | Test on Windows | Windows-specific issues |
| `./scripts/run_tests.sh --docker all` | Test all platforms | Before pushing |
| `./scripts/test_docker_quick.sh` | Quick Linux test | Development |
| `./scripts/test_docker_full.sh` | Full cross-platform | Pre-release |

### Development Commands

| Command | Description | Use Case |
|---------|-------------|----------|
| `./scripts/docker_manager.sh shell linux` | Interactive Linux shell | Debugging |
| `./scripts/docker_manager.sh shell windows` | Interactive Windows shell | Windows debugging |
| `./scripts/docker_manager.sh build all` | Rebuild all images | After dependencies change |
| `./scripts/docker_manager.sh health linux` | Check container health | Troubleshooting |

### CI Simulation

| Command | Description | Use Case |
|---------|-------------|----------|
| `./scripts/simulate_ci.sh --fast` | Quick CI simulation | Regular checks |
| `./scripts/simulate_ci.sh --full` | Full CI pipeline | Before important releases |
| `./scripts/simulate_ci.sh --stage test` | Run specific CI stage | Focused testing |

### Maintenance Commands

| Command | Description | Use Case |
|---------|-------------|----------|
| `./scripts/docker_manager.sh clean` | Clean containers/volumes | Free disk space |
| `./scripts/docker_manager.sh stats` | Show resource usage | Monitor performance |
| `./scripts/docker_manager.sh logs linux` | View container logs | Debugging |

## 🔧 Advanced Usage

### Interactive Development

Get an interactive shell in a container for debugging:

```bash
# Linux development environment
./scripts/docker_manager.sh shell linux

# Windows development environment
./scripts/docker_manager.sh shell windows
```

Inside the container, you can:
- Run individual tests: `python -m pytest tests/python/test_basic_app.py -v`
- Debug C code: `gdb ./build/test_router`
- Check memory usage: `valgrind python -m pytest tests/python/`
- Modify code and test immediately

### Performance Benchmarking

```bash
# Run performance benchmarks on all platforms
./scripts/docker_manager.sh benchmark all

# Linux-only benchmarks
./scripts/docker_manager.sh benchmark linux
```

### Generate Test Reports

```bash
# Generate comprehensive test report
./scripts/docker_test_report.sh --full --platform all

# JSON format for automation
./scripts/docker_test_report.sh --json --output results.json
```

## 🐧 Linux Container Details

**Base Image**: Ubuntu 22.04
**Python**: 3.10+
**C Compiler**: GCC with build-essential
**Memory Allocator**: jemalloc (preloaded)
**Build System**: CMake + make

**Environment Variables**:
- `LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2`
- `PYTHONUNBUFFERED=1`
- `FORCE_COLOR=1`

## 🪟 Windows Container Details

**Base Image**: Windows Server 2022
**Python**: 3.11+
**C Compiler**: Visual Studio 2022 Build Tools
**Memory Allocator**: jemalloc via vcpkg
**Build System**: CMake + MSBuild

**Environment Variables**:
- `CMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake`
- `CATZILLA_JEMALLOC_PATH=C:/vcpkg/installed/x64-windows/bin/jemalloc.dll`

## 🛠️ Troubleshooting

### Docker Not Found
```bash
# Install Docker Desktop
# https://www.docker.com/products/docker-desktop
```

### Windows Containers Not Working
Windows containers require Docker Desktop with Windows containers enabled:
1. Right-click Docker Desktop tray icon
2. Select "Switch to Windows containers"
3. Restart Docker Desktop

### Build Failures
```bash
# Clean and rebuild
./scripts/docker_manager.sh clean
./scripts/docker_manager.sh rebuild all
```

### Permission Issues (Linux/macOS)
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Container Memory Issues
```bash
# Check resource usage
./scripts/docker_manager.sh stats

# Increase Docker memory limits in Docker Desktop
```

## 📊 Performance Expectations

| Platform | Build Time | Test Time | Container Size |
|----------|------------|-----------|----------------|
| Linux | ~2-3 min | ~30-60s | ~800MB |
| Windows | ~10-15 min | ~60-120s | ~4GB |

*Note: Windows containers are larger and slower due to the Windows base image*

## 🔄 Workflow Integration

### Daily Development
```bash
# Before starting work
./scripts/run_tests.sh --docker linux

# After making changes
./scripts/test_docker_quick.sh

# Before committing
./scripts/simulate_ci.sh --fast
```

### Before Pushing
```bash
# Full cross-platform verification
./scripts/simulate_ci.sh --full --report
```

### Release Preparation
```bash
# Comprehensive testing with report
./scripts/docker_test_report.sh --full --platform all
./scripts/docker_manager.sh benchmark all
```

## 🎯 Best Practices

1. **Use Linux for rapid iteration** - It's faster than Windows containers
2. **Run full cross-platform tests before pushing** - Catch platform-specific issues
3. **Clean up regularly** - Docker images can consume significant disk space
4. **Use interactive shells for debugging** - More efficient than CI debugging
5. **Generate reports for releases** - Document testing coverage

## 🔗 Integration with CI/CD

This Docker setup exactly mirrors our GitHub Actions CI environment:

- Same OS versions (Ubuntu 22.04, Windows Server 2022)
- Same Python versions
- Same build tools and dependencies
- Same jemalloc configuration
- Same test execution patterns

## 📈 Monitoring & Metrics

```bash
# Real-time container stats
./scripts/docker_manager.sh stats

# Container health checks
./scripts/docker_manager.sh health linux
./scripts/docker_manager.sh health windows

# View detailed logs
./scripts/docker_manager.sh logs linux
```

## 🤝 Contributing

When contributing to Catzilla:

1. **Always test locally first** using this Docker setup
2. **Run the full CI simulation** before creating PRs
3. **Include test reports** for significant changes
4. **Update Docker files** if adding new dependencies

## 📝 Configuration Files

- **docker-compose.yml**: Container orchestration and networking
- **linux/Dockerfile**: Linux container build instructions
- **windows/Dockerfile**: Windows container build instructions
- **linux/test.sh**: Linux test execution script
- **windows/test.bat**: Windows test execution script

## 🆘 Support

If you encounter issues:

1. Check this README for common solutions
2. View container logs: `./scripts/docker_manager.sh logs`
3. Try cleaning and rebuilding: `./scripts/docker_manager.sh clean && ./scripts/docker_manager.sh rebuild all`
4. Create an issue with the output of `./scripts/docker_test_report.sh --full`

---

**Happy cross-platform testing! 🚀**
