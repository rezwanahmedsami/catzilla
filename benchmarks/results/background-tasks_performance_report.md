# Catzilla Ubackground-tasks Category Performance Report

## Test Configuration
- **Category**: background-tasks
- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
- **Date**: Sun Aug 17 21:15:11 +06 2025

## Performance Results

| Framework | Endpoint | Requests/sec | Avg Latency | 99% Latency |
|-----------|----------|--------------|-------------|-------------|
| catzilla | background-tasks_batch_processing | 13218.62 | 9.00ms | 76.22ms |
| catzilla | background-tasks_email_task | 12814.10 | 9.05ms | 56.53ms |
| catzilla | background-tasks_health_check | 10783.09 | 10.46ms | 19.88ms |
| catzilla | background-tasks_parallel_tasks | 12879.02 | 8.97ms | 59.76ms |
| catzilla | background-tasks_queue_processing | 13534.65 | 8.09ms | 12.35ms |
| catzilla | background-tasks_scheduled_task | 13462.16 | 8.09ms | 11.59ms |
| catzilla | background-tasks_simple_task | 14118.15 | 7.80ms | 11.90ms |
| django | background-tasks_batch_processing | 451.50 | 217.69ms | 346.45ms |
| django | background-tasks_email_task | 481.48 | 205.18ms | 233.07ms |
| django | background-tasks_health_check | 568.81 | 173.85ms | 203.98ms |
| django | background-tasks_parallel_tasks | 434.82 | 225.68ms | 376.08ms |
| django | background-tasks_queue_processing | 454.39 | 217.27ms | 250.17ms |
| django | background-tasks_scheduled_task | 458.61 | 215.34ms | 246.15ms |
| django | background-tasks_simple_task | 503.00 | 196.29ms | 225.23ms |
| fastapi | background-tasks_batch_processing | 1197.11 | 83.00ms | 153.35ms |
| fastapi | background-tasks_email_task | 1125.58 | 88.51ms | 174.91ms |
| fastapi | background-tasks_health_check | 1112.34 | 90.03ms | 189.96ms |
| fastapi | background-tasks_parallel_tasks | 991.04 | 100.64ms | 198.87ms |
| fastapi | background-tasks_queue_processing | 1149.72 | 86.31ms | 150.86ms |
| fastapi | background-tasks_scheduled_task | 1164.26 | 85.53ms | 164.56ms |
| fastapi | background-tasks_simple_task | 1164.55 | 85.56ms | 155.86ms |
| flask | background-tasks_batch_processing | 2.47 | 3.22ms | 7.52ms |
| flask | background-tasks_email_task | 1441.67 | 46.49ms | 63.07ms |
| flask | background-tasks_health_check | 1177.23 | 68.27ms | 83.42ms |
| flask | background-tasks_parallel_tasks | 1.79 | 6.08ms | 21.02ms |
| flask | background-tasks_queue_processing | 873.51 | 44.47ms | 54.79ms |
| flask | background-tasks_scheduled_task | 0.00 | 0.00us | 0.00us |
| flask | background-tasks_simple_task | 0.59 | 2.70ms | 5.35ms |

## Catzilla Performance Advantage

This report shows how Catzilla performs compared to other frameworks in the **background-tasks** category.
