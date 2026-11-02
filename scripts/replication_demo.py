"""
Lab 6: демонстрація Replication Lag, Stale Read та Read-After-Write (Sticky Routing).

Використання:  python scripts/replication_demo.py
Щоб Stale Read було добре видно, спершу ввімкніть штучну затримку репліки:
    $env:REPLICA_LAG="3s"; docker compose up -d db-replica
"""
import json
import time
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

API = "http://localhost:8080/api/v1"

plain = urllib.request.build_opener()  # "інший користувач": без cookie
sticky = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))  # "браузер": зберігає cookie


def create_board(opener, title):
    req = urllib.request.Request(
        f"{API}/boards", data=json.dumps({"title": title}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with opener.open(req) as r:
        return json.loads(r.read())


def find_in_list(opener, title):
    """GET /boards?search=... (eventual read). Повертає (знайдено?, вузол БД)."""
    url = f"{API}/boards?search={urllib.parse.quote(title)}"
    with opener.open(url) as r:
        return len(json.loads(r.read())) > 0, r.headers["X-DB-Node"]


# 0. Стан реплікації
with plain.open(f"{API}/lab/replication") as r:
    status = json.loads(r.read())
print("== 0. Стан реплікації")
print("   replicas on primary:", status["primary"]["replicas"] if isinstance(status["primary"], dict) else status["primary"])

# 1. Stale Read: записали на Primary -> одразу читаємо з Replica
print("\n== 1. Stale Read (клієнт БЕЗ sticky-cookie)")
title = f"lab6-stale-{time.time_ns()}"
t0 = time.perf_counter()
create_board(plain, title)
found, node = find_in_list(plain, title)
print(f"   одразу після POST: знайдено={found}  X-DB-Node={node}   <- {'STALE READ!' if not found else 'репліка вже встигла'}")
while not found:  # опитуємо, поки репліка не наздожене Primary
    time.sleep(0.1)
    found, node = find_in_list(plain, title)
print(f"   дошка з'явилась на {node} через ~{(time.perf_counter() - t0) * 1000:.0f} мс  (= Replication Lag)")

# 2. Read-After-Write: Session Sticky Routing
print("\n== 2. Read-After-Write (клієнт ЗІ sticky-cookie)")
title = f"lab6-sticky-{time.time_ns()}"
create_board(sticky, title)
found, node = find_in_list(sticky, title)
print(f"   одразу після POST: знайдено={found}  X-DB-Node={node}   <- cookie rw_sticky => читання з Primary")
print("   чекаємо 6 с (STICKY_TTL_SEC=5), cookie зникає...")
time.sleep(6)
found, node = find_in_list(sticky, title)
print(f"   після TTL:         знайдено={found}  X-DB-Node={node}   <- знову читаємо з Replica")
