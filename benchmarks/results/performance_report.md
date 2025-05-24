# 🚀 Catzilla Performance Benchmark Report

Generated on: 2025-05-25 02:00:29

## 📊 Executive Summary

- **Best Overall RPS Framework**: catzilla
- **Best Overall Latency Framework**: catzilla
- **Catzilla vs Fastapi**: +258.2% requests/sec

## 📈 Detailed Framework Statistics

### Catzilla
- **Avg RPS**: 5600 (±1590)
- **Max RPS**: 8130
- **Avg Latency**: 25.36ms (±8.69)
- **Min Latency**: 14.90ms

### Fastapi
- **Avg RPS**: 1564 (±451)
- **Max RPS**: 2087
- **Avg Latency**: 69.11ms (±23.76)
- **Min Latency**: 47.78ms

## 🎯 Endpoint Performance Breakdown

### Complex Json
🥇 **Catzilla**: 5156 req/s
🥈 **Fastapi**: 1344 req/s

### Hello World
🥇 **Catzilla**: 8130 req/s
🥈 **Fastapi**: 2087 req/s

### Json Response
🥇 **Catzilla**: 5165 req/s
🥈 **Fastapi**: 1844 req/s

### Path Params
🥇 **Catzilla**: 5765 req/s
🥈 **Fastapi**: 1621 req/s

### Query Params
🥇 **Catzilla**: 3785 req/s
🥈 **Fastapi**: 923 req/s

## ⚙️ Test Configuration

- **Duration**: 10s
- **Connections**: 100
- **Threads**: 4
- **Tool**: wrk
