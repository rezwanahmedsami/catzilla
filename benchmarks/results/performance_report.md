# 🚀 Catzilla Performance Benchmark Report

Generated on: 2025-08-10 15:14:11

## 📊 Executive Summary

- **Best Overall RPS Framework**: catzilla
- **Best Overall Latency Framework**: unknown
- **Catzilla vs Fastapi**: +453.1% requests/sec
- **Catzilla vs Flask**: +2140.7% requests/sec

## 📈 Detailed Framework Statistics

### Catzilla
- **Avg RPS**: 12231 (±4833)
- **Max RPS**: 16752
- **Avg Latency**: 12.33ms (±23.78)
- **Min Latency**: 2.91ms

### Fastapi
- **Avg RPS**: 2211 (±701)
- **Max RPS**: 2584
- **Avg Latency**: 29.31ms (±27.81)
- **Min Latency**: 18.44ms

### Flask
- **Avg RPS**: 546 (±315)
- **Max RPS**: 864
- **Avg Latency**: 73.15ms (±31.78)
- **Min Latency**: 52.79ms

### Unknown
- **Avg RPS**: 0 (±0)
- **Max RPS**: 0
- **Avg Latency**: 0.00ms (±0.00)
- **Min Latency**: 0.00ms

## 🎯 Endpoint Performance Breakdown

### Unknown
🥇 **Unknown**: 0 req/s

### Sqlalchemy-Di Complex Db Operations
🥇 **Catzilla**: 12770 req/s
🥈 **Fastapi**: 2436 req/s
🥉 **Flask**: 152 req/s

### Sqlalchemy-Di Complex Di Chain
🥇 **Catzilla**: 12664 req/s
🥈 **Fastapi**: 2466 req/s
🥉 **Flask**: 864 req/s

### Sqlalchemy-Di Db Posts List
🥇 **Catzilla**: 11772 req/s
🥈 **Fastapi**: 2472 req/s
🥉 **Flask**: 732 req/s

### Sqlalchemy-Di Db User Detail
🥇 **Catzilla**: 13367 req/s
🥈 **Fastapi**: 2375 req/s
🥉 **Flask**: 747 req/s

### Sqlalchemy-Di Db Users List
🥇 **Catzilla**: 14257 req/s
🥈 **Fastapi**: 2474 req/s
🥉 **Flask**: 65 req/s

### Sqlalchemy-Di Health Check
🥇 **Catzilla**: 943 req/s
🥈 **Fastapi**: 483 req/s
🥉 **Flask**: 316 req/s

### Sqlalchemy-Di Simple Di
🥇 **Catzilla**: 16752 req/s
🥈 **Fastapi**: 2584 req/s
🥉 **Flask**: 749 req/s

### Sqlalchemy-Di Transient Di
🥇 **Catzilla**: 15327 req/s
🥈 **Fastapi**: 2401 req/s
🥉 **Flask**: 742 req/s

## ⚙️ Test Configuration

- **Duration**: 5s
- **Connections**: 50
- **Threads**: 4
- **Tool**: wrk
