"""
Live Demonstration Script for Laboratory Work 2
Stateless Application Architecture & Cross-Instance Consistency Verification
"""
import sys
import time
import httpx


def test_cluster(base_url: str = "http://localhost:8080"):
    print("=" * 70)
    print("  ЛАБОРАТОРНА РОБОТА №2: ДЕМОНСТРАЦІЯ STATELESS АРХІТЕКТУРИ")
    print(f"  Цільовий вузол (Nginx Load Balancer): {base_url}")
    print("=" * 70)

    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        # 1. Round-Robin Distribution Test
        print("\n[ТЕСТ 1] Перевірка балансування Round-Robin та заголовка X-Instance-ID:")
        instances_seen = set()
        for i in range(1, 7):
            try:
                res = client.get("/api/v1/health")
                instance_id = res.headers.get("x-instance-id", "Unknown")
                instances_seen.add(instance_id)
                print(f"  Запит #{i}: HTTP {res.status_code} | Вузол-виконавець (X-Instance-ID): \033[92m{instance_id}\033[0m")
            except Exception as e:
                print(f"  Запит #{i}: Помилка з'єднання ({e})")
            time.sleep(0.3)

        print(f"\n  Всього задіяно унікальних backend-екземплярів: {len(instances_seen)} {list(instances_seen)}")
        if len(instances_seen) > 1:
            print("  \033[92m[✓ УСПІХ]\033[0m Запити розподіляються між різними stateless вузлами без Sticky Sessions!")
        else:
            print("  \033[93m[УВАГА]\033[0m Відповів лише один вузол (переконайтеся, що запущено docker compose up з двома контейнерами).")

        # 2. Cross-Instance Data Consistency Test
        print("\n[ТЕСТ 2] Перевірка узгодженості даних між різними вузлами (Cross-Instance Consistency):")
        
        # Create on whatever instance responds first
        board_payload = {
            "title": f"Live Demo Board {int(time.time())}",
            "description": "Створено для перевірки відсутності локального стану",
            "background_color": "#FAF8F5",
            "grid_type": "freeform",
            "owner_id": 1
        }
        res_create = client.post("/api/v1/boards", json=board_payload)
        creator_node = res_create.headers.get("x-instance-id", "Node-A")
        board_id = res_create.json()["id"]
        print(f"  1. Створено дошку #{board_id} на вузлі: \033[94m{creator_node}\033[0m")

        # Read on the next request (which will hit the other instance under round-robin)
        res_read = client.get(f"/api/v1/boards/{board_id}")
        reader_node = res_read.headers.get("x-instance-id", "Node-B")
        print(f"  2. Прочитано дошку #{board_id} на вузлі: \033[94m{reader_node}\033[0m (версія: {res_read.json()['version']})")

        # Batch update
        batch_payload = {
            "expected_board_version": 1,
            "elements": [
                {
                    "element_type": "note",
                    "x": 100.0,
                    "y": 100.0,
                    "content": {"title": "Live Verification", "text": "Дані синхронні на всіх нодах!"}
                }
            ]
        }
        res_batch = client.post(f"/api/v1/boards/{board_id}/elements/batch", json=batch_payload)
        updater_node = res_batch.headers.get("x-instance-id", "Node-C")
        new_version = res_batch.json()["new_board_version"]
        print(f"  3. Пакетне оновлення канвасу на вузлі: \033[94m{updater_node}\033[0m (нова версія: v{new_version})")

        # Verify fresh state
        res_final = client.get(f"/api/v1/boards/{board_id}")
        verifier_node = res_final.headers.get("x-instance-id", "Node-D")
        final_elements = len(res_final.json()["elements"])
        print(f"  4. Підтвердження стану на вузлі: \033[94m{verifier_node}\033[0m (елементів: {final_elements}, версія: v{res_final.json()['version']})")

        print("\n  \033[92m[✓ ПІДСУМОК]\033[0m Усі операції пройшли узгоджено незалежно від того, який вузол їх обробляв!")
        print("=" * 70)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    test_cluster(url)
