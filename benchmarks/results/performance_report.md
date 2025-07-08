# 🚀 Catzilla Performance Benchmark Report

Generated on: 2025-07-08 13:48:55

## 📊 Executive Summary

- **Best Overall RPS Framework**: catzilla
- **Best Overall Latency Framework**: catzilla
- **Catzilla vs Django**: +2011.9% requests/sec
- **Catzilla vs Fastapi**: +422.6% requests/sec
- **Catzilla vs Flask**: +1810.8% requests/sec

## 📈 Detailed Framework Statistics

### Catzilla
- **Avg RPS**: 10652 (±4931)
- **Max RPS**: 20793
- **Avg Latency**: 13.88ms (±5.11)
- **Min Latency**: 5.26ms

### Django
- **Avg RPS**: 504 (±270)
- **Max RPS**: 677
- **Avg Latency**: 145.94ms (±23.61)
- **Min Latency**: 113.70ms

### Fastapi
- **Avg RPS**: 2038 (±663)
- **Max RPS**: 2912
- **Avg Latency**: 54.75ms (±21.49)
- **Min Latency**: 34.25ms

### Flask
- **Avg RPS**: 557 (±330)
- **Max RPS**: 847
- **Avg Latency**: 128.66ms (±25.27)
- **Min Latency**: 112.85ms

## 🎯 Endpoint Performance Breakdown

### Complex Json
🥇 **Catzilla**: 9657 req/s
🥈 **Fastapi**: 1773 req/s
🥉 **Flask**: 310 req/s
   **Django**: 25 req/s

### Hello World
🥇 **Catzilla**: 20793 req/s
🥈 **Fastapi**: 2912 req/s
🥉 **Flask**: 847 req/s
   **Django**: 596 req/s

### Json Response
🥇 **Catzilla**: 14165 req/s
🥈 **Fastapi**: 2294 req/s
🥉 **Django**: 619 req/s
   **Flask**: 236 req/s

### Path Params
🥇 **Catzilla**: 12214 req/s
🥈 **Fastapi**: 2098 req/s
🥉 **Django**: 677 req/s

### Query Params
🥇 **Catzilla**: 7793 req/s
🥈 **Fastapi**: 1115 req/s
🥉 **Flask**: 837 req/s
   **Django**: 605 req/s

### Query Validation
🥇 **Catzilla**: 7348 req/s

### Validate Product Model
🥇 **Catzilla**: 6475 req/s

### Validate User Model
🥇 **Catzilla**: 6773 req/s

## ⚙️ Test Configuration

- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
