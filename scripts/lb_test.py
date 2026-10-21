"""
Lab 3: навантажувальний тест через балансувальник.
Використання:  python scripts/lb_test.py [path] [requests] [concurrency]
Приклад:       python scripts/lb_test.py "/api/v1/lab/work?cpu_ms=10" 1000 20
"""
import sys
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8080"  # єдина точка входу (Nginx)
path = sys.argv[1] if len(sys.argv) > 1 else "/health"
total = int(sys.argv[2]) if len(sys.argv) > 2 else 300
concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 10


def one_request(_):
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=30) as resp:
            instance = resp.headers.get("X-Instance-ID")  # який вузол обробив запит
    except Exception:
        instance = "ERROR"  # 5xx або обрив з'єднання
    return instance, (time.perf_counter() - start) * 1000


started = time.perf_counter()
with ThreadPoolExecutor(concurrency) as pool:
    results = list(pool.map(one_request, range(total)))
elapsed = time.perf_counter() - started

latencies = sorted(ms for _, ms in results)
p50 = latencies[len(latencies) // 2]
p99 = latencies[int(len(latencies) * 0.99) - 1]

print(f"{path}  requests={total}  concurrency={concurrency}")
print(f"throughput={total / elapsed:.1f} req/s   p50={p50:.1f} ms   p99={p99:.1f} ms")
for instance, count in sorted(Counter(i for i, _ in results).items()):
    avg = sum(ms for i, ms in results if i == instance) / count
    print(f"  {instance:<22} {count:>6}  {count * 100 / total:5.1f}%   avg={avg:.1f} ms")
