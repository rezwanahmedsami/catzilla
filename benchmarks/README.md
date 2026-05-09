# Catzilla Benchmarking Guide

This directory contains the benchmark runner, comparison servers, result artifacts, and visualization tooling used to measure Catzilla against FastAPI, Flask, and Django.

## Benchmark Claim

The benchmark suite in this repository currently shows Catzilla leading the comparison frameworks in both single-worker and 10-worker direct HTTP benchmarks.

## Current Highlights

### Single / 1 Worker

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | 50,610 | 2.22ms | 28.26MB | `basic_hello_world` at 72,249 RPS |
| FastAPI | 8,537 | 12.74ms | 31.50MB | `basic_hello_world` at 11,132 RPS |
| Flask | 3,004 | 48.91ms | 46.45MB | `basic_hello_world` at 3,094 RPS |
| Django | 2,780 | 54.80ms | 52.92MB | `basic_hello_world` at 2,866 RPS |

![Single worker benchmark summary](results/overall_single_1w_performance_summary.png)

### Multi / 10 Workers

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | 180,023 | 6.03ms | 303.53MB | `basic_hello_world` at 212,426 RPS |
| FastAPI | 42,890 | 25.26ms | 350.71MB | `basic_hello_world` at 55,122 RPS |
| Flask | 5,488 | 177.89ms | 288.68MB | `basic_json_response` at 5,537 RPS |
| Django | 5,549 | 175.11ms | 349.75MB | `basic_query_params` at 5,623 RPS |

![10 worker benchmark summary](results/overall_multi_10w_performance_summary.png)

## Benchmark Guidance

- Use the project virtual environment when running benchmarks or the visualizer. From the repository root, prefer `/Users/rezwanahmedsami/devwork/catzilla/.venv/bin/python` over a bare `python` command.
- Use `10s` runs for publishable numbers and README/report screenshots. Use `1s` runs only for smoke checks while iterating.
- In `--worker-mode multi`, `--connections` means **connections per worker**. Total offered load is `workers * connections_per_worker`.
- In Catzilla multi-worker mode, `--threads` is the **requested** total client thread count. The runner may raise the **effective** wrk thread count so each backend worker receives load.
- `peak_memory_mb` is the peak summed RSS of the benchmark server process tree while `wrk` is active. For multi-worker Catzilla, that includes the launcher/proxy plus the backend worker processes.
- Compare single-worker and multi-worker charts separately. Do not average them together for marketing or release claims.

## Quick Start

### 1. Activate the Environment

```bash
cd /Users/rezwanahmedsami/devwork/catzilla
source .venv/bin/activate
```

### 2. Run Single-Worker Basic Benchmarks

```bash
cd benchmarks
./run_all.sh --type basic --worker-mode single --duration 10s
```

### 3. Run 10-Worker Basic Benchmarks

```bash
cd /Users/rezwanahmedsami/devwork/catzilla/benchmarks
./run_all.sh --type basic --worker-mode multi --workers 10 --duration 10s
```

### 4. Regenerate Visual Reports

```bash
cd /Users/rezwanahmedsami/devwork/catzilla
/Users/rezwanahmedsami/devwork/catzilla/.venv/bin/python ./benchmarks/tools/visualize_results.py
```

## Recommended Commands

### Smoke Check

```bash
cd /Users/rezwanahmedsami/devwork/catzilla/benchmarks
./run_all.sh --type basic --framework catzilla --worker-mode single --duration 1s
```

### Full Basic Comparison

```bash
cd /Users/rezwanahmedsami/devwork/catzilla/benchmarks
./run_all.sh --type basic --duration 10s
./run_all.sh --type basic --worker-mode multi --workers 10 --duration 10s
```

### Per-Worker Load Override

```bash
cd /Users/rezwanahmedsami/devwork/catzilla/benchmarks
./run_all.sh --type basic --worker-mode multi --workers 10 --connections 200 --duration 10s
```

That command applies `200` concurrent connections to each worker, for `2000` total connections.

## Output Files

The benchmark pipeline emits both raw and summarized artifacts:

- `results/*_single_1w.json` and `results/*_multi_10w.json` contain structured metrics including `requests_per_sec`, latency, and `peak_memory_mb`.
- `results/benchmark_summary.json` stores the merged dataset used by the visualizer.
- `results/overall_single_1w_performance_summary.png` and `results/overall_multi_10w_performance_summary.png` are the best headline charts for single-worker and 10-worker results.
- `results/overall_single_1w_memory_comparison.png` and `results/overall_multi_10w_memory_comparison.png` show memory comparison directly.
- `results/basic_single_1w_performance_analysis.png` and `results/basic_multi_10w_performance_analysis.png` include endpoint-by-endpoint RPS, latency, and peak-memory panels.
- `results/transparent_performance_report.md` is the generated markdown report that embeds the benchmark story.
- `/Users/rezwanahmedsami/devwork/catzilla/PERFORMANCE_REPORT_v0.2.2.md` is the current release-facing benchmark report.

## Interpretation Notes

- Single-worker results are the cleanest way to compare raw framework overhead.
- 10-worker results show how each framework behaves when the load shape is scaled out.
- Peak memory should be read together with RPS and latency. Lower memory is useful, but lower memory with poor throughput is not a performance win.
- The current benchmark suite measures localhost performance. Treat it as framework overhead and runtime efficiency comparison, not a universal internet-scale guarantee.

## Directory Structure

```text
benchmarks/
├── run_all.sh
├── run_enhanced_benchmarks.py
├── run_enhanced_feature_benchmarks.sh
├── servers/
├── shared/
├── tools/
│   ├── system_info.py
│   └── visualize_results.py
└── results/
```
