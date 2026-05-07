# Catzilla Ubackground-tasks Category Performance Report

## Test Configuration
- **Category**: background-tasks
- **Duration**: 1s
- **Connections**: 10
- **Threads**: 2
- **Tool**: wrk
- **Date**: Fri May  8 01:37:02 +06 2026

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | background-tasks_health_check | 50041.25 | 201.51us | 497.00us |
| catzilla | background-tasks_queue_stats | 48642.33 | 207.94us | 538.00us |
| catzilla | background-tasks_task_listing | 44019.72 | 228.18us | 514.00us |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **background-tasks** category.
