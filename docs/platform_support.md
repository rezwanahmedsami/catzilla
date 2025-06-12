# Platform Support

## Memory Allocators by Platform

Catzilla uses different memory allocators optimized for each platform to provide the best performance characteristics.

### Current Support Matrix

| Platform | Memory Allocator | Performance Level | Status |
|----------|-----------------|-------------------|---------|
| **Linux** | jemalloc | High Performance ⚡ | ✅ Full Support |
| **macOS** | jemalloc | High Performance ⚡ | ✅ Full Support |
| **Windows** | malloc (standard) | Standard Performance | ✅ Stable Support |

### Performance Characteristics

#### Linux & macOS (jemalloc)
- **Optimized for**: High-concurrency web applications
- **Benefits**:
  - Reduced memory fragmentation
  - Better multi-threading performance
  - Advanced memory profiling capabilities
  - Optimized for server workloads
- **Use Cases**: Production web servers, high-traffic applications, memory-intensive tasks

#### Windows (malloc)
- **Optimized for**: General-purpose applications
- **Benefits**:
  - Reliable and well-tested
  - No additional dependencies
  - Consistent cross-platform behavior
  - Suitable for development and moderate workloads
- **Use Cases**: Development environments, small to medium applications, Windows desktop apps

## Runtime Detection

Catzilla automatically detects and uses the best available allocator for your platform:

```python
from catzilla import Catzilla

# Check what allocator is available
if Catzilla.jemalloc_available():
    print("Using jemalloc for optimal performance")
    app = Catzilla(use_jemalloc=True)
else:
    print("Using standard malloc - reliable performance")
    app = Catzilla(use_jemalloc=False)

# Or let Catzilla decide automatically (recommended)
app = Catzilla()  # Uses best available allocator
```

## Platform-Specific Notes

### Linux
- jemalloc is built from source during installation
- Requires `cmake` and `build-essential` packages
- Automatically enabled for production deployments

### macOS
- jemalloc is built using system tools
- Requires Xcode command line tools
- Homebrew dependencies handled automatically

### Windows
- Uses system malloc for reliability and simplicity
- No additional build dependencies required
- Full feature compatibility maintained
- **Future**: jemalloc support planned for future releases based on user demand

## Performance Impact

Based on benchmarks across platforms:

- **Linux/macOS with jemalloc**: 15-30% performance improvement in memory-intensive workloads
- **Windows with malloc**: Baseline performance, excellent stability
- **Cross-platform**: API and feature parity maintained across all allocators

## Development Recommendations

### For Production Deployments
- **Recommended**: Linux or macOS for maximum performance
- **Acceptable**: Windows for moderate workloads
- **Best Practice**: Test on your target platform

### For Development
- Any platform works excellently
- Windows developers get full feature access
- Memory behavior consistent across platforms for development

## Future Roadmap

### Windows jemalloc Support
- **Status**: Under consideration
- **Timeline**: Based on user demand and feedback
- **Approach**: Will likely use pre-built binaries (vcpkg) when implemented
- **Impact**: Zero breaking changes - purely additive

### Memory Allocator Extensions
- Custom allocator plugin system
- Advanced memory profiling tools
- Platform-specific optimizations

## Troubleshooting

### Build Issues
If you encounter memory allocator build issues:

1. **Linux**: Ensure `build-essential` and `cmake` are installed
2. **macOS**: Install Xcode command line tools
3. **Windows**: No action needed - malloc fallback is automatic

### Performance Questions
- **Q**: Why doesn't Windows use jemalloc?
- **A**: Windows jemalloc builds are complex and provide marginal benefits for typical Windows use cases. We prioritize reliability and development velocity.

- **Q**: Can I force jemalloc on Windows?
- **A**: Not currently supported. Use Linux or macOS for jemalloc performance benefits.

### Reporting Issues
If you experience platform-specific issues:
1. Include your platform and Python version
2. Run the built-in diagnostics
3. Report on GitHub with the `platform-support` label

---

*Last updated: June 2025*
