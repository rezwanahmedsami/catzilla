# 🚀 Catzilla Performance Benchmark Report

Generated on: 2025-07-08 11:26:02

## 📊 Executive Summary

- **Best Overall RPS Framework**: catzilla
- **Best Overall Latency Framework**: catzilla
- **Catzilla vs Django**: +402.5% requests/sec
- **Catzilla vs Fastapi**: +259.4% requests/sec
- **Catzilla vs Flask**: +324.4% requests/sec

## 📈 Detailed Framework Statistics

### Catzilla
- **Avg RPS**: 21947 (±6861)
- **Max RPS**: 35678
- **Avg Latency**: 5.07ms (±1.31)
- **Min Latency**: 2.97ms

### Django
- **Avg RPS**: 4367 (±268)
- **Max RPS**: 4671
- **Avg Latency**: 22.93ms (±1.44)
- **Min Latency**: 21.47ms

### Fastapi
- **Avg RPS**: 6106 (±1690)
- **Max RPS**: 7979
- **Avg Latency**: 17.75ms (±6.25)
- **Min Latency**: 12.65ms

### Flask
- **Avg RPS**: 5172 (±299)
- **Max RPS**: 5558
- **Avg Latency**: 19.34ms (±1.14)
- **Min Latency**: 17.93ms

## 🎯 Endpoint Performance Breakdown

### Complex Json
🥇 **Catzilla**: 21178 req/s
🥈 **Fastapi**: 5550 req/s
🥉 **Flask**: 4976 req/s
   **Django**: 4298 req/s

### Hello World
🥇 **Catzilla**: 35678 req/s
🥈 **Fastapi**: 7979 req/s
🥉 **Flask**: 5558 req/s
   **Django**: 4671 req/s

### Json Response
🥇 **Catzilla**: 26723 req/s
🥈 **Fastapi**: 6938 req/s
🥉 **Flask**: 5379 req/s
   **Django**: 4474 req/s

### Path Params
🥇 **Catzilla**: 24734 req/s
🥈 **Fastapi**: 6548 req/s
🥉 **Flask**: 5129 req/s
   **Django**: 4441 req/s

### Query Params
🥇 **Catzilla**: 16251 req/s
🥈 **Flask**: 4817 req/s
🥉 **Django**: 3952 req/s
   **Fastapi**: 3515 req/s

### Query Validation
🥇 **Catzilla**: 18630 req/s

### Validate Product Model
🥇 **Catzilla**: 16328 req/s

### Validate User Model
🥇 **Catzilla**: 16052 req/s

## ⚙️ Test Configuration

- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
