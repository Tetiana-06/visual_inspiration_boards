### A_read_3inst_low

| VUs | Throughput (RPS) | Avg, ms | p50, ms | p95, ms | p99, ms | Error Rate, % |
|---|---|---|---|---|---|---|
| 1 | 221.1 | 4.4 | 3.6 | 8.3 | 9.4 | 0.00 |
| 2 | 411.1 | 4.7 | 3.8 | 9.0 | 10.3 | 0.00 |
| 4 | 618.8 | 6.3 | 5.0 | 12.5 | 14.7 | 0.00 |
| 8 | 680.8 | 11.6 | 9.6 | 22.4 | 26.8 | 0.00 |
| 16 | 670.4 | 23.7 | 20.0 | 41.7 | 54.1 | 0.00 |

```mermaid
xychart-beta
  title "A_read_3inst_low: Throughput, RPS"
  x-axis "VUs" [1, 2, 4, 8, 16]
  y-axis "RPS"
  bar [221.1, 411.1, 618.8, 680.8, 670.4]
```

```mermaid
xychart-beta
  title "A_read_3inst_low: Latency p50 / p95 / p99, ms"
  x-axis "VUs" [1, 2, 4, 8, 16]
  y-axis "ms"
  line [3.6, 3.8, 5.0, 9.6, 20.0]
  line [8.3, 9.0, 12.5, 22.4, 41.7]
  line [9.4, 10.3, 14.7, 26.8, 54.1]
```
