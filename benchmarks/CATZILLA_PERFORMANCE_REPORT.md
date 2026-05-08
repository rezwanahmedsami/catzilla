# Catzilla Benchmark Highlights

**Date:** May 8, 2026  
**Framework:** Catzilla v0.2.0  
**Environment:** macOS arm64, direct `wrk` benchmarks against Catzilla, FastAPI, Flask, and Django

## Claim

Catzilla is built to be the **world's fastest Python web framework**.
The benchmark suite in this repository shows it leading the comparison frameworks in both single-worker and 10-worker direct HTTP runs.

## Single / 1 Worker

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | 52,700 | 2.16ms | 28.52MB | `basic_hello_world` at 76,169 RPS |
| FastAPI | 8,400 | 13.01ms | 31.45MB | `basic_hello_world` at 10,990 RPS |
| Flask | 2,993 | 48.76ms | 46.33MB | `basic_hello_world` at 3,087 RPS |
| Django | 2,731 | 55.77ms | 52.88MB | `basic_hello_world` at 2,854 RPS |

![Single worker overall performance summary](results/overall_single_1w_performance_summary.png)

![Single worker peak memory comparison](results/overall_single_1w_memory_comparison.png)

## Multi / 10 Workers

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | 166,877 | 6.84ms | 270.37MB | `basic_hello_world` at 197,947 RPS |
| FastAPI | 37,585 | 29.49ms | 352.40MB | `basic_hello_world` at 49,098 RPS |
| Flask | 5,613 | 173.19ms | 288.23MB | `basic_path_params` at 5,672 RPS |
| Django | 5,656 | 171.23ms | 349.32MB | `basic_complex_json` at 5,736 RPS |

![10 worker overall performance summary](results/overall_multi_10w_performance_summary.png)

![10 worker peak memory comparison](results/overall_multi_10w_memory_comparison.png)

## What Matters

- Catzilla leads the suite in both single-worker and 10-worker throughput.
- Catzilla keeps the lowest latency in both modes.
- Catzilla also keeps peak memory below FastAPI and Django in both modes, and below Flask in the 10-worker run.
- The strongest headline numbers come from `basic_hello_world`, but the lead remains across JSON, path-parameter, and query-parameter endpoints.

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
