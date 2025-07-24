# 🚀 Catzilla Feature-Based Benchmarking System

A comprehensive benchmarking framework for testing Catzilla's performance across different feature categories compared to other Python web frameworks.

## 📋 Overview

This benchmarking system goes beyond simple HTTP tests to evaluate real-world performance across specific framework features:

- **Middleware Performance** - Sync vs async middleware implementations
- **Dependency Injection** - Service resolution across different scopes
- **Async Operations** - Hybrid async/sync performance
- **Database Integration** - ORM and database operations
- **Validation** - Auto-validation engine performance
- **File Operations** - Upload and static file serving
- **Background Tasks** - Task queue performance
- **Real-World Scenarios** - Complete application benchmarks

## 🏗️ Directory Structure

```
benchmarks/
├── servers/                          # Feature-specific server implementations
│   ├── basic/                        # Basic HTTP benchmarks
│   │   ├── catzilla_server.py        # Catzilla basic server
│   │   ├── fastapi_server.py         # FastAPI basic server
│   │   └── endpoints.json            # Endpoint configurations
│   ├── middleware/                   # Middleware performance
│   │   ├── catzilla_middleware.py    # Catzilla middleware server
│   │   ├── fastapi_middleware.py     # FastAPI middleware server
│   │   └── endpoints.json            # Middleware test endpoints
│   ├── dependency_injection/         # DI system performance
│   │   ├── catzilla_di.py           # Catzilla DI server
│   │   ├── fastapi_di.py            # FastAPI DI server
│   │   └── endpoints.json            # DI test endpoints
│   └── async_operations/             # Async/sync hybrid tests
├── shared/                           # Shared utilities
│   └── shared_endpoints.py          # Common endpoint definitions
├── tools/                            # Benchmarking tools
│   ├── system_info.py               # System information collection
│   └── visualize_results.py         # Results visualization
├── results/                          # Benchmark results
├── run_feature_benchmarks.sh        # Main shell-based runner
└── run_benchmarks.py               # Enhanced Python runner
```

## 🚀 Quick Start

### 1. Check Dependencies

```bash
# Check if all dependencies are available
python run_benchmarks.py --check
```

### 2. List Available Features

```bash
# See all available feature categories
python run_benchmarks.py --list
```

### 3. Run Specific Feature Benchmark

```bash
# Run middleware benchmarks
python run_benchmarks.py --feature middleware

# Run dependency injection benchmarks
python run_benchmarks.py --feature dependency_injection

# Run basic HTTP benchmarks
python run_benchmarks.py --feature basic
```

### 4. Run All Benchmarks

```bash
# Run comprehensive benchmarks for all features
python run_benchmarks.py --all
```

## 🔧 Advanced Usage

### Using the Shell Runner Directly

```bash
# Run specific feature with custom port
./run_feature_benchmarks.sh middleware 8100

# Run all features
./run_feature_benchmarks.sh all
```

### Custom Port Ranges

```bash
# Start benchmarks from port 9000
python run_benchmarks.py --all --port 9000

# Run middleware benchmarks on port 8500
python run_benchmarks.py --feature middleware --port 8500
```

### Generate Reports Only

```bash
# Generate reports from existing results
python run_benchmarks.py --report-only
```

## 📊 Results and Reporting

### Result Files

Each benchmark run generates:
- `{framework}_{endpoint_name}.txt` - Raw wrk output
- `{framework}_{endpoint_name}.json` - Structured results
- `benchmark_summary.json` - Comprehensive summary
- `system_info.json` - System specifications

### Visualization

Performance charts are automatically generated showing:
- Requests per second comparison
- Latency distribution
- Memory usage patterns
- Feature-specific metrics

### Example Result Structure

```json
{
  "framework": "catzilla",
  "endpoint": "/middleware-heavy",
  "endpoint_name": "heavy_middleware",
  "method": "GET",
  "requests_per_sec": "15240.56",
  "avg_latency": "3.2ms",
  "p99_latency": "8.5ms",
  "feature_category": "middleware"
}
```

## 🎯 Feature Categories

### Basic Benchmarks
- HTTP request handling fundamentals
- JSON serialization/deserialization
- Path and query parameter processing
- Auto-validation performance

### Middleware Benchmarks
- Authentication middleware overhead
- CORS handling performance
- Rate limiting efficiency
- Request/response logging impact
- Async operations in middleware

### Dependency Injection Benchmarks
- Service resolution speed
- Scope management (singleton, request, transient)
- Complex dependency graphs
- Repository pattern performance

### Async Operations Benchmarks
- Mixed async/sync handler performance
- Concurrent operation handling
- Event loop efficiency
- Thread pool utilization

## 🔬 Benchmark Methodology

### Load Testing Configuration
- **Duration**: 10 seconds per test
- **Connections**: 100 concurrent connections
- **Threads**: 4 worker threads
- **Warmup**: 3 seconds before measurement

### Metrics Collected
- Requests per second
- Average latency
- 99th percentile latency
- Transfer rate
- Memory usage
- CPU utilization

### Framework Comparison
Current frameworks tested:
- **Catzilla** - C-accelerated with jemalloc optimization
- **FastAPI** - Async-first Python framework
- **Flask** - Traditional WSGI framework
- **Django** - Full-featured web framework (planned)

## 📈 Performance Targets

Catzilla aims to demonstrate:
- **25%+ faster** middleware processing than FastAPI
- **40%+ faster** dependency injection resolution
- **30%+ lower** memory usage with jemalloc
- **20%+ better** database integration performance
- **Comparable** async operation performance to specialized frameworks

## 🛠️ Adding New Features

### 1. Create Feature Directory
```bash
mkdir benchmarks/servers/new_feature
```

### 2. Add Server Implementations
```python
# benchmarks/servers/new_feature/catzilla_new_feature.py
# Implement Catzilla server for the new feature

# benchmarks/servers/new_feature/fastapi_new_feature.py
# Implement FastAPI server for comparison
```

### 3. Define Endpoints
```json
// benchmarks/servers/new_feature/endpoints.json
{
  "feature_category": "new_feature",
  "description": "Description of the new feature",
  "endpoints": [
    {
      "path": "/test",
      "name": "test_endpoint",
      "method": "GET",
      "description": "Test endpoint description"
    }
  ]
}
```

### 4. Run Benchmarks
```bash
python run_benchmarks.py --feature new_feature
```

## 🔍 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill existing processes
lsof -ti:8000 | xargs kill -9

# Use different port range
python run_benchmarks.py --all --port 9000
```

#### Missing Dependencies
```bash
# Install wrk (macOS)
brew install wrk

# Install wrk (Ubuntu)
sudo apt-get install wrk

# Install Python dependencies
pip install matplotlib pandas seaborn psutil
```

#### Server Start Failures
- Check Python path configuration
- Verify framework installations
- Review server logs in results directory

### Debug Mode

Enable verbose output:
```bash
# Use shell runner with verbose output
./run_feature_benchmarks.sh middleware 8000

# Check individual server functionality
python benchmarks/servers/middleware/catzilla_middleware.py --port 8100
```

## 📝 Contributing

### Adding Framework Support
1. Create server implementation following existing patterns
2. Ensure consistent endpoint definitions
3. Add argument parsing for port/host configuration
4. Test with benchmark runner

### Improving Benchmarks
1. Add realistic business logic scenarios
2. Implement proper error handling
3. Include comprehensive validation tests
4. Document performance expectations

## 📊 Compatibility

This system maintains compatibility with the original benchmarking infrastructure:
- Same result format as `benchmarks_old/`
- Compatible with existing visualization tools
- Reuses system information collection
- Maintains same wrk-based testing methodology

## 🎉 Getting Started

1. **Check your setup**: `python run_benchmarks.py --check`
2. **List features**: `python run_benchmarks.py --list`
3. **Run a quick test**: `python run_benchmarks.py --feature basic`
4. **Run full suite**: `python run_benchmarks.py --all`
5. **View results**: Check `benchmarks/results/` directory

Happy benchmarking! 🚀
