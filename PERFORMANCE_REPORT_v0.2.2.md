# Catzilla Framework Performance Report v0.2.2

**Report Date:** May 9, 2026
**Version:** v0.2.2
**Benchmark Tool:** wrk
**Environment:** macOS arm64, localhost direct HTTP benchmarks
**Published Scope:** basic endpoint suite only
**Worker Configurations:** Single / 1 worker and Multi / 10 workers
**Frameworks Compared:** Catzilla, FastAPI, Flask, Django

## Executive Summary

This report covers the benchmark artifacts generated for the `v0.2.2` release.
In the current published basic suite, Catzilla leads FastAPI, Flask, and Django in every tested endpoint for both single-worker and 10-worker runs.

### Headline Numbers

- **Single / 1 worker average throughput:** **50,610 req/s**
- **Single / 1 worker best endpoint:** **`basic_hello_world` at 72,249 req/s**
- **Single / 1 worker average latency:** **2.22ms**
- **Single / 1 worker average peak memory:** **28.26MB**
- **Single / 1 worker lead over FastAPI:** **5.9x average throughput**

- **Multi / 10 workers average throughput:** **180,023 req/s**
- **Multi / 10 workers best endpoint:** **`basic_hello_world` at 212,426 req/s**
- **Multi / 10 workers average latency:** **6.03ms**
- **Multi / 10 workers average peak memory:** **303.53MB**
- **Multi / 10 workers lead over FastAPI:** **4.2x average throughput**

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
| Catzilla | **50,610** | **2.22ms** | **28.26MB** | `basic_hello_world` at **72,249** |
| FastAPI | 8,537 | 12.74ms | 31.50MB | `basic_hello_world` at 11,132 |
| Flask | 3,004 | 48.91ms | 46.45MB | `basic_hello_world` at 3,094 |
| Django | 2,780 | 54.80ms | 52.92MB | `basic_hello_world` at 2,866 |

### Multi / 10 Workers

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | **180,023** | **6.03ms** | **303.53MB** | `basic_hello_world` at **212,426** |
| FastAPI | 42,890 | 25.26ms | 350.71MB | `basic_hello_world` at 55,122 |
| Flask | 5,488 | 177.89ms | 288.68MB | `basic_json_response` at 5,537 |
| Django | 5,549 | 175.11ms | 349.75MB | `basic_query_params` at 5,623 |

## Endpoint-by-Endpoint Throughput

### Single / 1 Worker Requests per Second

| Endpoint | Catzilla | FastAPI | Flask | Django |
|----------|----------|---------|-------|--------|
| `basic_complex_json` | **41,649** | 7,680 | 2,975 | 2,764 |
| `basic_hello_world` | **72,249** | 11,132 | 3,094 | 2,866 |
| `basic_json_response` | **57,767** | 9,870 | 3,047 | 2,816 |
| `basic_path_params` | **49,678** | 9,214 | 3,013 | 2,806 |
| `basic_query_params` | **31,707** | 4,786 | 2,891 | 2,646 |

### Multi / 10 Workers Requests per Second

| Endpoint | Catzilla | FastAPI | Flask | Django |
|----------|----------|---------|-------|--------|
| `basic_complex_json` | **167,951** | 38,680 | 5,432 | 5,567 |
| `basic_hello_world` | **212,426** | 55,122 | 5,495 | 5,473 |
| `basic_json_response` | **197,326** | 49,678 | 5,537 | 5,528 |
| `basic_path_params` | **184,445** | 45,680 | 5,449 | 5,554 |
| `basic_query_params` | **137,966** | 25,290 | 5,527 | 5,623 |

## Key Takeaways

- Catzilla leads the current published basic suite in both worker modes.
- `basic_hello_world` is the strongest current headline endpoint, but the lead remains across complex JSON, path parameters, and query parameters.
- `basic_query_params` is the lowest-throughput endpoint for Catzilla in the published suite, but it still materially outperforms the comparison frameworks.
- Catzilla keeps the lowest average latency in both worker modes and lower average peak memory than FastAPI and Django in both published runs.

## Visualizations

### Single / 1 Worker

![Single worker overall performance summary](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_single_1w_performance_summary.png)

![Single worker requests per second](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_single_1w_requests_per_second.png)

![Single worker latency comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_single_1w_latency_comparison.png)

![Single worker memory comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_single_1w_memory_comparison.png)

![Single worker performance heatmap](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_single_1w_performance_heatmap.png)

![Single worker basic analysis](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/basic_single_1w_performance_analysis.png)

### Multi / 10 Workers

![10 worker overall performance summary](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_multi_10w_performance_summary.png)

![10 worker requests per second](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_multi_10w_requests_per_second.png)

![10 worker latency comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_multi_10w_latency_comparison.png)

![10 worker memory comparison](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_multi_10w_memory_comparison.png)

![10 worker performance heatmap](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/overall_multi_10w_performance_heatmap.png)

![10 worker basic analysis](https://raw.githubusercontent.com/rezwanahmedsami/catzilla/v0.2.2/benchmarks/results/basic_multi_10w_performance_analysis.png)

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