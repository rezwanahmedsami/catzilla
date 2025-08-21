# Catzilla Streaming Tests

This directory contains tests for the Catzilla streaming implementation.

## Directory Structure

- `c/` - C tests for the core streaming implementation
- `python/` - Python tests for the Python API

## Running Tests

### C Tests

Build and run the C tests:

```bash
# From the project root
make -f tests/Makefile c-tests
```

### Python Tests

Run the Python tests:

```bash
# From the project root
make -f tests/Makefile py-tests
```

### All Tests

Run all tests:

```bash
# From the project root
make -f tests/Makefile
```

## Test Descriptions

### C Tests

- `test_streaming_detection` - Tests the detection of streaming responses
- `test_stream_create_destroy` - Tests creation and cleanup of streaming contexts
- `test_stream_write_chunk` - Tests writing data chunks to a stream
- `test_stream_finish` - Tests finishing a stream
- `test_stream_abort` - Tests aborting a stream
- `test_send_streaming_response` - Tests sending streaming response headers
- `test_ring_buffer` - Tests the ring buffer implementation for backpressure

### Python Tests

- `TestStreamingResponse` - Tests the `StreamingResponse` class functionality
  - Creation with different content types
  - Content type handling
  - Binary and text content
  - Integration with server
- `TestStreamingPerformance` - Tests the performance of streaming responses

## Adding New Tests

### C Tests

Add new C tests to the `tests/c/test_streaming.c` file following the Unity test framework pattern:

```c
void test_new_feature(void) {
    // Test setup

    // Test assertions
    TEST_ASSERT_EQUAL(expected, actual);

    // Test cleanup
}

// Add to main():
RUN_TEST(test_new_feature);
```

### Python Tests

Add new Python tests by adding methods to the test classes in `tests/python/test_streaming.py` or by creating new test classes:

```python
def test_new_feature(self):
    """Test description."""
    # Test code
    self.assertEqual(expected, actual)
```
