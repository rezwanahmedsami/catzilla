# 🚀 Catzilla Performance Benchmark Report

Generated on: 2025-05-25 18:39:27

## 📊 Executive Summary

- **Best Overall RPS Framework**: catzilla
- **Best Overall Latency Framework**: catzilla
- **Catzilla vs Django**: +1655.7% requests/sec
- **Catzilla vs Fastapi**: +530.6% requests/sec
- **Catzilla vs Flask**: +1960.8% requests/sec

## 📈 Detailed Framework Statistics

### Catzilla
- **Avg RPS**: 9907 (±1503)
- **Max RPS**: 11962
- **Avg Latency**: 13.82ms (±2.71)
- **Min Latency**: 9.85ms

### Django
- **Avg RPS**: 564 (±129)
- **Max RPS**: 673
- **Avg Latency**: 143.75ms (±23.24)
- **Min Latency**: 124.69ms

### Fastapi
- **Avg RPS**: 1571 (±362)
- **Max RPS**: 1868
- **Avg Latency**: 68.28ms (±21.98)
- **Min Latency**: 53.63ms

### Flask
- **Avg RPS**: 481 (±472)
- **Max RPS**: 988
- **Avg Latency**: 104.48ms (±11.50)
- **Min Latency**: 88.82ms

## 🎯 Endpoint Performance Breakdown

### Complex Json
🥇 **Catzilla**: 11962 req/s
🥈 **Fastapi**: 1703 req/s
🥉 **Django**: 673 req/s
   **Flask**: 34 req/s

### Hello World
🥇 **Catzilla**: 10313 req/s
🥈 **Fastapi**: 1734 req/s
🥉 **Flask**: 974 req/s
   **Django**: 576 req/s

### Json Response
🥇 **Catzilla**: 10390 req/s
🥈 **Fastapi**: 1603 req/s
🥉 **Django**: 628 req/s
   **Flask**: 68 req/s

### Path Params
🥇 **Catzilla**: 8235 req/s
🥈 **Fastapi**: 1868 req/s
🥉 **Flask**: 988 req/s

### Query Params
🥇 **Catzilla**: 8634 req/s
🥈 **Fastapi**: 946 req/s
🥉 **Django**: 380 req/s
   **Flask**: 341 req/s

## ⚙️ Test Configuration

- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
