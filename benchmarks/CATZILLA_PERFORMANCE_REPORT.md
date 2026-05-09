# Catzilla Benchmark Highlights

**Date:** May 9, 2026  
**Framework:** Catzilla v0.2.2  
**Environment:** macOS arm64, direct `wrk` benchmarks against Catzilla, FastAPI, Flask, and Django

## Claim

The benchmark suite in this repository currently shows Catzilla leading the comparison frameworks in both single-worker and 10-worker direct HTTP runs.

## Single / 1 Worker

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | 50,610 | 2.22ms | 28.26MB | `basic_hello_world` at 72,249 RPS |
| FastAPI | 8,537 | 12.74ms | 31.50MB | `basic_hello_world` at 11,132 RPS |
| Flask | 3,004 | 48.91ms | 46.45MB | `basic_hello_world` at 3,094 RPS |
| Django | 2,780 | 54.80ms | 52.92MB | `basic_hello_world` at 2,866 RPS |

![Single worker overall performance summary](results/overall_single_1w_performance_summary.png)

![Single worker peak memory comparison](results/overall_single_1w_memory_comparison.png)

## Multi / 10 Workers

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | 180,023 | 6.03ms | 303.53MB | `basic_hello_world` at 212,426 RPS |
| FastAPI | 42,890 | 25.26ms | 350.71MB | `basic_hello_world` at 55,122 RPS |
| Flask | 5,488 | 177.89ms | 288.68MB | `basic_json_response` at 5,537 RPS |
| Django | 5,549 | 175.11ms | 349.75MB | `basic_query_params` at 5,623 RPS |

![10 worker overall performance summary](results/overall_multi_10w_performance_summary.png)

![10 worker peak memory comparison](results/overall_multi_10w_memory_comparison.png)

## What Matters

- Catzilla leads the suite in both single-worker and 10-worker throughput.
- Catzilla keeps the lowest latency in both modes.
- Catzilla keeps peak memory below FastAPI and Django in both modes.
- The strongest headline numbers come from `basic_hello_world`, but the lead remains across complex JSON, path-parameter, and query-parameter endpoints.

## Reproduce These Results

```bash
cd /Users/rezwanahmedsami/devwork/catzilla
source .venv/bin/activate

cd benchmarks
./run_all.sh --type basic --worker-mode single --duration 10s
./run_all.sh --type basic --worker-mode multi --workers 10 --duration 10s

cd ..
/Users/rezwanahmedsami/devwork/catzilla/.venv/bin/python ./benchmarks/tools/visualize_results.py
```

## Related Files

- `results/benchmark_summary.json`
- `results/transparent_performance_report.md`
- `results/basic_single_1w_performance_analysis.png`
- `results/basic_multi_10w_performance_analysis.png`
