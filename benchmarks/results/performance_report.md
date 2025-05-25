# 🚀 Catzilla Performance Benchmark Report

Generated on: 2025-05-25 16:37:11

## 📊 Executive Summary

- **Best Overall RPS Framework**: catzilla
- **Best Overall Latency Framework**: catzilla
- **Catzilla vs Django**: +693.9% requests/sec
- **Catzilla vs Fastapi**: +649.3% requests/sec
- **Catzilla vs Flask**: +547.1% requests/sec

## 📈 Detailed Framework Statistics

### Catzilla
- **Avg RPS**: 16820 (±5060)
- **Max RPS**: 24637
- **Avg Latency**: 6.37ms (±1.78)
- **Min Latency**: 4.06ms

### Django
- **Avg RPS**: 2119 (±137)
- **Max RPS**: 2297
- **Avg Latency**: 47.11ms (±3.10)
- **Min Latency**: 43.31ms

### Fastapi
- **Avg RPS**: 2245 (±588)
- **Max RPS**: 2921
- **Avg Latency**: 47.40ms (±14.72)
- **Min Latency**: 34.13ms

### Flask
- **Avg RPS**: 2599 (±171)
- **Max RPS**: 2851
- **Avg Latency**: 38.41ms (±2.49)
- **Min Latency**: 34.90ms

## 🎯 Endpoint Performance Breakdown

### Complex Json
🥇 **Catzilla**: 13803 req/s
🥈 **Flask**: 2516 req/s
🥉 **Django**: 2104 req/s
   **Fastapi**: 2003 req/s

### Hello World
🥇 **Catzilla**: 24637 req/s
🥈 **Fastapi**: 2921 req/s
🥉 **Flask**: 2851 req/s
   **Django**: 2297 req/s

### Json Response
🥇 **Catzilla**: 18408 req/s
🥈 **Flask**: 2664 req/s
🥉 **Fastapi**: 2616 req/s
   **Django**: 2159 req/s

### Path Params
🥇 **Catzilla**: 15775 req/s
🥈 **Flask**: 2570 req/s
🥉 **Fastapi**: 2292 req/s
   **Django**: 2117 req/s

### Query Params
🥇 **Catzilla**: 11474 req/s
🥈 **Flask**: 2394 req/s
🥉 **Django**: 1916 req/s
   **Fastapi**: 1391 req/s

## ⚙️ Test Configuration

- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
