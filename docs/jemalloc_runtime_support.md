# Catzilla v0.2.0 Runtime Jemalloc Support

## Overview

Catzilla v0.2.0 introduces **conditional runtime jemalloc support** with static linking, providing seamless memory allocator selection through the `use_jemalloc` parameter. This system automatically handles jemalloc availability and falls back gracefully to standard malloc when jemalloc is not available.

## Key Features

### 🚀 **Runtime Allocator Selection**
- Use `use_jemalloc=True/False` to control memory allocator choice
- Automatic fallback to malloc when jemalloc is unavailable
- Zero-configuration deployment across different environments

### 🔧 **Static Linking System**
- jemalloc is built from source using git submodules
- No external dependencies or library conflicts
- Self-contained builds with conditional compilation

### 📊 **Enhanced Memory Monitoring**
- Real-time allocator information and statistics
- Memory profiling with efficiency trends
- Arena-specific allocation tracking

## API Usage

### Basic Usage

```python
from catzilla import Catzilla

# Default: Use jemalloc if available, fallback to malloc
app = Catzilla(use_jemalloc=True)

print(f"Using jemalloc: {app.has_jemalloc}")
print(f"Current allocator: {app.get_allocator_info()['current_allocator']}")
```

### Check Availability Before Creating Instance

```python
# Static method to check jemalloc availability
if Catzilla.jemalloc_available():
    app = Catzilla(use_jemalloc=True, memory_profiling=True)
    print("Using jemalloc with profiling")
else:
    app = Catzilla(use_jemalloc=False)
    print("Using standard malloc")
```

### Explicit Malloc Usage

```python
# Force malloc usage (disable jemalloc)
app = Catzilla(use_jemalloc=False)
```

### Production Configuration

```python
# Conditional production setup
jemalloc_available = Catzilla.jemalloc_available()

app = Catzilla(
    use_jemalloc=jemalloc_available,
    memory_profiling=jemalloc_available,
    auto_memory_tuning=jemalloc_available,
    production=True
)
```

## New Methods and Properties

### Static Methods

- `Catzilla.jemalloc_available()` - Check jemalloc build availability
- `Catzilla.get_available_allocators()` - List available allocators

### Instance Methods

- `app.get_allocator_info()` - Get current allocator information
- `app.get_memory_stats()` - Enhanced memory statistics with allocator info

### Properties

- `app.has_jemalloc` - True if jemalloc is actually being used
- `app.use_jemalloc` - True if jemalloc was requested (may fallback)

## Memory Statistics

The enhanced `get_memory_stats()` method now includes:

```python
stats = app.get_memory_stats()
print(stats)
# {
#     "allocator": "jemalloc",           # Current allocator
#     "jemalloc_available": True,        # Build supports jemalloc
#     "jemalloc_requested": True,        # User requested jemalloc
#     "jemalloc_enabled": True,          # Actually using jemalloc
#     "allocated_mb": 15.2,              # Memory allocated (if jemalloc)
#     "fragmentation_percent": 2.1,      # Memory fragmentation
#     "profiling_enabled": True          # Memory profiling status
# }
```

## Allocator Information

```python
info = app.get_allocator_info()
print(info)
# {
#     "current_allocator": "jemalloc",
#     "jemalloc_available": True,
#     "jemalloc_requested": True,
#     "jemalloc_enabled": True,
#     "memory_profiling": True,
#     "auto_memory_tuning": True,
#     "can_switch_allocator": False,
#     "status": "initialized"
# }
```

## Build Configuration

### CMake Options

```bash
# Build with jemalloc support (default)
cmake -DCATZILLA_USE_JEMALLOC=ON -DCATZILLA_BUILD_JEMALLOC=ON ..

# Build without jemalloc (malloc only)
cmake -DCATZILLA_USE_JEMALLOC=OFF ..

# Debug build with jemalloc debugging
cmake -DCATZILLA_JEMALLOC_DEBUG=ON ..
```

### Git Submodule

The jemalloc source is included as a git submodule:

```bash
# Initialize submodules when cloning
git clone --recursive https://github.com/rezwanahmedsami/catzilla.git

# Or update existing repository
git submodule update --init --recursive
```

## Deployment Scenarios

### Scenario 1: Full jemalloc Support
- Build includes jemalloc (static linking)
- Runtime: `use_jemalloc=True` → Uses jemalloc
- Performance: Maximum memory efficiency

### Scenario 2: Fallback Environment
- Build includes jemalloc but environment issues
- Runtime: `use_jemalloc=True` → Falls back to malloc
- Performance: Standard malloc performance

### Scenario 3: Malloc-only Build
- Build compiled without jemalloc (`CATZILLA_USE_JEMALLOC=OFF`)
- Runtime: `use_jemalloc=True` → Uses malloc (no jemalloc available)
- Performance: Standard malloc performance

### Scenario 4: Explicit Malloc
- Any build configuration
- Runtime: `use_jemalloc=False` → Uses malloc
- Performance: Standard malloc performance

## Error Handling

The system provides graceful error handling:

1. **Build-time**: If jemalloc submodule is missing, builds with malloc support only
2. **Runtime**: If jemalloc initialization fails, automatic fallback to malloc
3. **User feedback**: Clear console messages about allocator status
4. **Statistics**: Detailed error information in memory stats

## Migration from v0.1.x

### Old Code (v0.1.x)
```python
# Limited jemalloc support
app = Catzilla()  # jemalloc if available, undefined behavior if not
```

### New Code (v0.2.0)
```python
# Explicit control with fallback
app = Catzilla(use_jemalloc=True)  # Automatic fallback to malloc

# Check what actually happened
print(f"Using: {app.get_allocator_info()['current_allocator']}")
```

## Performance Impact

| Allocator | Memory Usage | Allocation Speed | Fragmentation | Best For |
|-----------|-------------|------------------|---------------|----------|
| jemalloc  | 30% less    | Very fast       | Low          | Production, high-load |
| malloc    | Standard    | Fast            | Higher       | Development, compatibility |

## Troubleshooting

### jemalloc Not Available
If `Catzilla.jemalloc_available()` returns `False`:

1. **Check build**: Ensure `CATZILLA_USE_JEMALLOC=ON` during cmake
2. **Check submodule**: Run `git submodule update --init --recursive`
3. **Check dependencies**: Install required build tools (autoconf, etc.)

### Runtime Fallback
If `app.has_jemalloc` is `False` despite `use_jemalloc=True`:

1. **Check logs**: Console will show fallback reason
2. **Check environment**: Some systems have jemalloc TLS issues
3. **Check statistics**: Use `app.get_memory_stats()` for detailed info

## Advanced Configuration

### Custom Memory Profiling

```python
app = Catzilla(
    use_jemalloc=True,
    memory_profiling=True,
    auto_memory_tuning=True,
    memory_stats_interval=60  # Profile every 60 seconds
)

# Monitor memory trends
@app.get("/memory-trend")
def memory_trend():
    stats = app.get_memory_stats()
    return stats.get("memory_trend", "No trend data")
```

### Production Monitoring

```python
# Health check endpoint
@app.get("/health")
def health():
    allocator_info = app.get_allocator_info()
    memory_stats = app.get_memory_stats()
    
    return {
        "status": "healthy",
        "allocator": allocator_info["current_allocator"],
        "memory_efficiency": memory_stats.get("fragmentation_percent", 0) < 10,
        "jemalloc_working": allocator_info["jemalloc_enabled"]
    }
```

This new system provides maximum flexibility and reliability for memory management across different deployment environments while maintaining backward compatibility and providing clear feedback about the actual allocator being used.
