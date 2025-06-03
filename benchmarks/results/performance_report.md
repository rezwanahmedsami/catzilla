# 🚀 Catzilla Performance Benchmark Report

Generated on: 2025-06-03 12:07:19

## 📊 Executive Summary

- **Best Overall RPS Framework**: catzilla
- **Best Overall Latency Framework**: catzilla
- **Catzilla vs Django**: +705.3% requests/sec
- **Catzilla vs Fastapi**: +561.5% requests/sec
- **Catzilla vs Flask**: +589.6% requests/sec

## 📈 Detailed Framework Statistics

### Catzilla
- **Avg RPS**: 35908 (±13514)
- **Max RPS**: 60519
- **Avg Latency**: 3.21ms (±1.08)
- **Min Latency**: 1.69ms

### Django
- **Avg RPS**: 4459 (±313)
- **Max RPS**: 4828
- **Avg Latency**: 22.40ms (±1.63)
- **Min Latency**: 20.61ms

### Fastapi
- **Avg RPS**: 5429 (±1630)
- **Max RPS**: 7228
- **Avg Latency**: 20.14ms (±7.71)
- **Min Latency**: 13.76ms

### Flask
- **Avg RPS**: 5207 (±392)
- **Max RPS**: 5698
- **Avg Latency**: 19.19ms (±1.47)
- **Min Latency**: 17.44ms

## 🎯 Endpoint Performance Breakdown

### Complex Json
🥇 **Catzilla**: 35400 req/s
🥈 **Flask**: 5034 req/s
🥉 **Fastapi**: 4796 req/s
   **Django**: 4390 req/s

### Hello World
🥇 **Catzilla**: 60519 req/s
🥈 **Fastapi**: 7228 req/s
🥉 **Flask**: 5698 req/s
   **Django**: 4828 req/s

### Json Response
🥇 **Catzilla**: 45874 req/s
🥈 **Fastapi**: 6455 req/s
🥉 **Flask**: 5394 req/s
   **Django**: 4552 req/s

### Path Params
🥇 **Catzilla**: 45477 req/s
🥈 **Fastapi**: 5661 req/s
🥉 **Flask**: 5255 req/s
   **Django**: 4548 req/s

### Query Params
🥇 **Catzilla**: 23523 req/s
🥈 **Flask**: 4653 req/s
🥉 **Django**: 3976 req/s
   **Fastapi**: 3002 req/s

### Query Validation
🥇 **Catzilla**: 26738 req/s

### Validate Product Model
🥇 **Catzilla**: 25093 req/s

### Validate User Model
🥇 **Catzilla**: 24638 req/s

## ⚙️ Test Configuration

- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk

