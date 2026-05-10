# Catzilla Framework Performance Report

**Report Date:** May 11, 2026
**Published Benchmark Dataset:** latest generated artifacts (2026-05-11)
**Benchmark Tool:** wrk
**Environment:** macOS arm64, localhost direct HTTP benchmarks
**Published Scope:** basic endpoint suite only
**Worker Configurations:** Single / 1 worker and Multi / 10 workers
**Frameworks Compared:** Catzilla, FastAPI, Flask, Django

## Executive Summary

This report covers the latest published benchmark artifacts for Catzilla.
In the current published basic suite, Catzilla leads FastAPI, Flask, and Django in every tested endpoint for both single-worker and 10-worker runs.

### Headline Numbers

- **Single / 1 worker average throughput:** **55,731 req/s**
- **Single / 1 worker best endpoint:** **`basic_hello_world` at 82,817 req/s**
- **Single / 1 worker average latency:** **2.02ms**
- **Single / 1 worker average peak memory:** **30.77MB**
- **Single / 1 worker lead over FastAPI:** **2.6x average throughput**

- **Multi / 10 workers average throughput:** **159,997 req/s**
- **Multi / 10 workers best endpoint:** **`basic_hello_world` at 190,612 req/s**
- **Multi / 10 workers average latency:** **7.49ms**
- **Multi / 10 workers average peak memory:** **439.08MB**
- **Multi / 10 workers lead over FastAPI:** **2.1x average throughput**

## What This Report Covers

The current release-facing benchmark artifact set is intentionally narrow and reproducible:

- **Category:** `basic`
- **Endpoints:** hello world, JSON response, complex JSON, path parameters, query parameters
- **Tool:** `wrk`
- **Modes:** single-worker and 10-worker direct localhost runs

These results are best read as framework-overhead and runtime-efficiency comparisons on the same machine and workload shape. They are not universal production guarantees.

## Framework Summary

### Single / 1 Worker

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | **55,731** | **2.02ms** | **30.77MB** | `basic_hello_world` at **82,817** |
| FastAPI | 21,251 | 6.31ms | 58.17MB | `basic_hello_world` at 35,154 |
| Flask | 3,410 | 33.29ms | 70.84MB | `basic_hello_world` at 3,578 |
| Django | 3,337 | 34.33ms | 72.87MB | `basic_hello_world` at 3,493 |

### Multi / 10 Workers

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | **159,997** | **7.49ms** | **439.08MB** | `basic_hello_world` at **190,612** |
| FastAPI | 74,915 | 15.83ms | 636.17MB | `basic_hello_world` at 109,212 |
| Flask | 10,160 | 97.99ms | 420.09MB | `basic_json_response` at 10,243 |
| Django | 9,927 | 101.31ms | 442.02MB | `basic_hello_world` at 10,254 |

## Endpoint-by-Endpoint Throughput

### Single / 1 Worker Requests per Second

| Endpoint | Catzilla | FastAPI | Flask | Django |
|----------|----------|---------|-------|--------|
| `basic_complex_json` | **46,664** | 15,644 | 3,143 | 3,341 |
| `basic_hello_world` | **82,817** | 35,154 | 3,578 | 3,493 |
| `basic_json_response` | **57,035** | 27,477 | 3,496 | 3,258 |
| `basic_path_params` | **57,226** | 19,844 | 3,512 | 3,394 |
| `basic_query_params` | **34,912** | 8,135 | 3,322 | 3,200 |

### Multi / 10 Workers Requests per Second

| Endpoint | Catzilla | FastAPI | Flask | Django |
|----------|----------|---------|-------|--------|
| `basic_complex_json` | **149,439** | 61,666 | 10,106 | 9,703 |
| `basic_hello_world` | **190,612** | 109,212 | 10,324 | 10,254 |
| `basic_json_response` | **173,014** | 91,218 | 10,243 | 9,978 |
| `basic_path_params` | **161,648** | 75,415 | 10,199 | 9,939 |
| `basic_query_params` | **125,274** | 37,064 | 9,930 | 9,759 |

## Key Takeaways

- Catzilla leads the current published basic suite in both worker modes.
- `basic_hello_world` is the strongest current headline endpoint, and the lead remains across complex JSON, path parameters, and query parameters.
- `basic_query_params` is the lowest-throughput endpoint for Catzilla in the published suite, but it still materially outperforms the comparison frameworks.
- Catzilla keeps the lowest average latency in both worker modes and lower average peak memory than FastAPI and Django in the published runs.

## Visualizations

### Single / 1 Worker

![Single worker overall performance summary](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_single_1w_performance_summary.png)

![Single worker requests per second](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_single_1w_requests_per_second.png)

![Single worker latency comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_single_1w_latency_comparison.png)

![Single worker memory comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_single_1w_memory_comparison.png)

![Single worker performance heatmap](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_single_1w_performance_heatmap.png)

![Single worker basic analysis](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/basic_single_1w_performance_analysis.png)

### Multi / 10 Workers

![10 worker overall performance summary](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_multi_10w_performance_summary.png)

![10 worker requests per second](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_multi_10w_requests_per_second.png)

![10 worker latency comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_multi_10w_latency_comparison.png)

![10 worker memory comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_multi_10w_memory_comparison.png)

![10 worker performance heatmap](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/overall_multi_10w_performance_heatmap.png)

![10 worker basic analysis](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/main/benchmarks/results/basic_multi_10w_performance_analysis.png)

## Reproducing the Published Results

```bash
cd /Users/rezwanahmedsami/devwork/catzilla
source .venv/bin/activate

cd benchmarks
./run_all.sh --type basic --worker-mode single --duration 10s
./run_all.sh --type basic --worker-mode multi --workers 10 --duration 10s

cd ..
/Users/rezwanahmedsami/devwork/catzilla/.venv/bin/python ./benchmarks/tools/visualize_results.py
```

## Related Artifacts

- [benchmarks/results/basic_performance_report.md](benchmarks/results/basic_performance_report.md)
- [benchmarks/results/transparent_performance_report.md](benchmarks/results/transparent_performance_report.md)
- [benchmarks/results/benchmark_summary.json](benchmarks/results/benchmark_summary.json)
- [benchmarks/README.md](benchmarks/README.md)

## Interpretation Notes

- Compare single-worker and multi-worker results separately.
- The current release-facing charts are from localhost runs on one machine.
- Peak memory for multi-worker Catzilla includes the launcher/proxy plus backend worker processes during the run.
- If you want broader feature slices such as async operations, middleware, dependency injection, or validation, run those categories explicitly through the benchmark harness and publish them as separate artifact sets.