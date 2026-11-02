### B_write_3inst_low

| VUs | Throughput (RPS) | Avg, ms | p50, ms | p95, ms | p99, ms | Error Rate, % |
|---|---|---|---|---|---|---|
| 1 | 81.7 | 12.1 | 12.0 | 14.0 | 17.2 | 0.00 |
| 2 | 155.3 | 12.7 | 12.5 | 14.7 | 19.0 | 0.00 |
| 4 | 232.1 | 17.0 | 16.7 | 21.8 | 27.6 | 0.00 |
| 8 | 272.0 | 29.2 | 28.6 | 36.1 | 41.7 | 0.00 |
| 16 | 268.9 | 59.2 | 57.8 | 74.3 | 99.5 | 0.00 |

```mermaid
xychart-beta
  title "B_write_3inst_low: Throughput, RPS"
  x-axis "VUs" [1, 2, 4, 8, 16]
  y-axis "RPS"
  bar [81.7, 155.3, 232.1, 272.0, 268.9]
```

```mermaid
xychart-beta
  title "B_write_3inst_low: Latency p50 / p95 / p99, ms"
  x-axis "VUs" [1, 2, 4, 8, 16]
  y-axis "ms"
  line [12.0, 12.5, 16.7, 28.6, 57.8]
  line [14.0, 14.7, 21.8, 36.1, 74.3]
  line [17.2, 19.0, 27.6, 41.7, 99.5]
```
