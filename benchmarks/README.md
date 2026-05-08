# Catzilla Benchmarking Guide

This directory contains the benchmark runner, comparison servers, result artifacts, and visualization tooling used to measure Catzilla against FastAPI, Flask, and Django.

## Benchmark Claim

Catzilla is built to be the **world's fastest Python web framework**.
The benchmark suite in this repository currently shows Catzilla leading the comparison frameworks in both single-worker and 10-worker direct HTTP benchmarks.

## Current Highlights

### Single / 1 Worker

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | 52,700 | 2.16ms | 28.52MB | `basic_hello_world` at 76,169 RPS |
| FastAPI | 8,400 | 13.01ms | 31.45MB | `basic_hello_world` at 10,990 RPS |
| Flask | 2,993 | 48.76ms | 46.33MB | `basic_hello_world` at 3,087 RPS |
| Django | 2,731 | 55.77ms | 52.88MB | `basic_hello_world` at 2,854 RPS |

![Single worker benchmark summary](results/overall_single_1w_performance_summary.png)

### Multi / 10 Workers

| Framework | Avg RPS | Avg Latency | Avg Peak Memory | Best Endpoint |
|-----------|---------|-------------|-----------------|---------------|
| Catzilla | 166,877 | 6.84ms | 270.37MB | `basic_hello_world` at 197,947 RPS |
| FastAPI | 37,585 | 29.49ms | 352.40MB | `basic_hello_world` at 49,098 RPS |
| Flask | 5,613 | 173.19ms | 288.23MB | `basic_path_params` at 5,672 RPS |
| Django | 5,656 | 171.23ms | 349.32MB | `basic_complex_json` at 5,736 RPS |

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
