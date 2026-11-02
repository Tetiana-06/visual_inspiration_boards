"""
Lab 4: демонстрація Cache-Aside через балансувальник.
Використання:  python scripts/cache_demo.py [board_id] [rounds]
"""
import json
import sys
import time
import urllib.request

BASE_URL = "http://localhost:8080"
board_id = sys.argv[1] if len(sys.argv) > 1 else "1"
rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 30
URL = f"{BASE_URL}/api/v1/boards/{board_id}"


def get_board():
    start = time.perf_counter()
    with urllib.request.urlopen(URL) as resp:
        body = json.loads(resp.read())
        headers = resp.headers
    ms = (time.perf_counter() - start) * 1000
    return headers["X-Cache"], headers["X-Instance-ID"], ms, body


def patch_board(description):
    """Модифікація дошки => бекенд інвалідує ключ кешу."""
    req = urllib.request.Request(
        URL,
        data=json.dumps({"description": description}).encode(),
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    urllib.request.urlopen(req).read()


def show(label):
    cache_status, instance, ms, body = get_board()
    print(f"{label:<28} X-Cache={cache_status:<4}  {instance:<20} {ms:6.1f} ms  "
          f"version={body['version']}  description={body['description']!r}")


# 1. Hit / Miss
print("== 1. Hit / Miss")
patch_board("Lab 4 demo: start")  # гарантуємо холодний старт
show("GET (холодний)")
show("GET (повторний)")
show("GET (повторний)")

# 2. Інвалідація
print("== 2. Інвалідація")
patch_board(f"Lab 4 demo: changed at {time.strftime('%H:%M:%S')}")
print("PATCH /boards/{id}  -> cache.delete(key)")
show("GET після PATCH")
show("GET повторний")

# 3. Cold vs Hot latency
print(f"== 3. Cold vs Hot ({rounds} раундів)")
cold, hot = [], []
for _ in range(rounds):
    patch_board("Lab 4 demo: benchmark")
    cold.append(get_board()[2])  # MISS: БД + запис у Redis
    hot.extend(get_board()[2] for _ in range(5))  # HIT: лише Redis


def stats(name, values):
    values = sorted(values)
    print(f"{name}: n={len(values)}  avg={sum(values) / len(values):.1f} ms  "
          f"p50={values[len(values) // 2]:.1f} ms  p95={values[int(len(values) * 0.95) - 1]:.1f} ms")


stats("Cold (MISS)", cold)
stats("Hot  (HIT) ", hot)
