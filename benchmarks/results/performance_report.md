# 🚀 Catzilla Performance Benchmark Report

Generated on: 2025-05-25 18:09:30

## 📊 Executive Summary

- **Best Overall RPS Framework**: catzilla
- **Best Overall Latency Framework**: catzilla
- **Catzilla vs Django**: +671.2% requests/sec
- **Catzilla vs Fastapi**: +662.1% requests/sec
- **Catzilla vs Flask**: +540.7% requests/sec

## 📈 Detailed Framework Statistics

### Catzilla
- **Avg RPS**: 16818 (±5022)
- **Max RPS**: 24758
- **Avg Latency**: 6.37ms (±1.77)
- **Min Latency**: 4.07ms

### Django
- **Avg RPS**: 2181 (±132)
- **Max RPS**: 2339
- **Avg Latency**: 45.76ms (±2.87)
- **Min Latency**: 42.56ms

### Fastapi
- **Avg RPS**: 2207 (±531)
- **Max RPS**: 2844
- **Avg Latency**: 47.70ms (±13.54)
- **Min Latency**: 35.04ms

### Flask
- **Avg RPS**: 2625 (±168)
- **Max RPS**: 2875
- **Avg Latency**: 38.03ms (±2.38)
- **Min Latency**: 34.60ms

## 🎯 Endpoint Performance Breakdown

### Complex Json
🥇 **Catzilla**: 14842 req/s
🥈 **Flask**: 2521 req/s
🥉 **Django**: 2162 req/s
   **Fastapi**: 2008 req/s

### Hello World
🥇 **Catzilla**: 24758 req/s
🥈 **Flask**: 2875 req/s
🥉 **Fastapi**: 2844 req/s
   **Django**: 2339 req/s

### Json Response
🥇 **Catzilla**: 15754 req/s
🥈 **Flask**: 2672 req/s
🥉 **Fastapi**: 2421 req/s
   **Django**: 2208 req/s

### Path Params
🥇 **Catzilla**: 17590 req/s
🥈 **Flask**: 2624 req/s
🥉 **Fastapi**: 2341 req/s
   **Django**: 2219 req/s

### Query Params
🥇 **Catzilla**: 11145 req/s
🥈 **Flask**: 2431 req/s
🥉 **Django**: 1975 req/s
   **Fastapi**: 1419 req/s

## ⚙️ Test Configuration

- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
