# 📌 Visual Inspiration Boards (Collaborative Moodboard Platform)

> **Лабораторна робота № 1**: Проєктування архітектури (*System Design*) та реалізація базового прототипу розподіленої/модульної системи (MVP / Architectural Baseline).  
> **Лабораторна робота № 2**: Архітектура без стану (*Stateless Application Architecture*) та винесення стану системи (мульти-екземплярне розгортання, Round-Robin, `X-Instance-ID`, тестування стійкості).  
> **Естетика та інтерфейс:** Tiffany & Co. Aesthetic / Pinterest Vibe — бірюзові акценти `#0ABAB5`, стікери-нотатки, кольорові палітри, інтерактивний 2D-канвас із гострими кутами та підтримкою drag-and-drop.

---

## 🎨 Особливості платформи
- **Tiffany & Pinterest Aesthetic UI:**
  - Фірмова бірюзова палітра *Tiffany Blue* (`#0ABAB5`) та теплий фон `Warm Linen (#FAF8F5)`.
  - Суворі мінімалістичні форми з гострими кутами (0px border-radius).
  - Візуальні елементи канвасу: естетичні фотокартки, текстурні стікери, палітри кольорів із 5 зразками (копіювання HEX в один клік), цитати-стікери.
  - Інтерактивне переміщення мишкою (Drag-and-Drop) по 2D полотну.
  - Пакетна синхронізація (`Batch Sync`) з оптимістичним блокуванням (`Optimistic Concurrency Control`).
  - Відображення ідентифікатора активного stateless-вузла (`node: backend-instance-1 / 2`) у шапці.
- **Stateless Архітектура (Lab 2):**
  - **Interchangeable Workers:** 2 паралельні контейнери бекенду (`backend-1`, `backend-2`), повністю взаємозамінні, без in-memory залежностей.
  - **Round-Robin Load Balancing:** Nginx балансує трафік по черзі без Sticky Sessions.
  - **Node Identification:** заголовок відповіді `X-Instance-ID` дозволяє точно знати, який саме вузол обробив запит.
  - **Centralized Persistence & Distributed Cache:** спільні PostgreSQL 16 та Redis 7.
  - **Zero Data Loss on Node Death:** аварійна зупинка будь-якого екземпляра не призводить до втрати даних.

---

## 🚀 Як запустити проєкт

### Варіант 1: Декларативний запуск через Docker Compose (Рекомендовано для здачі)
Усе середовище (Nginx + 2 інстанси бекенду + PostgreSQL + Redis) піднімається **однією командою**:

```bash
docker compose up --build -d
```

Після запуску відкрийте у браузері:
- **Веб-інтерфейс:** [http://localhost](http://localhost) або [http://localhost:8080](http://localhost:8080)
- **Інтерактивна документація Swagger:** [http://localhost:8080/docs](http://localhost:8080/docs)
- **Health Check системи:** [http://localhost:8080/api/v1/health](http://localhost:8080/api/v1/health)

Зупинити стек із збереженням даних:
```bash
docker compose down
```

---

### Варіант 2: Локальний запуск (через Python Virtualenv)
Для швидкого запуску без підняття Docker сервіс автоматично використовує локальну базу даних:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python main.py
```
Застосунок буде доступний на [http://localhost:8000](http://localhost:8000).

---

## 🧪 Автоматизоване тестування

### 1. Запуск повного набору тестів pytest (Lab 1 + Lab 2):
```bash
.\.venv\Scripts\pytest -v
```
*(Перевіряє Healthcheck, CRUD, пакетну синхронізацію, права доступу, заголовок `X-Instance-ID`, міжвузлову узгодженість `Cross-Instance Consistency` та аварійну зупинку `Instance Loss Recovery`).*

### 2. Live-демонстрація кластера на захисті (Lab 2 Script):
При запущеному Docker Compose виконайте скрипт демонстрації:
```bash
python scripts/verify_cluster.py http://localhost:8080
```
Скрипт наочно продемонструє:
1. Почерговий Round-Robin розподіл запитів між `backend-instance-1` та `backend-instance-2`.
2. Створення даних на вузлі №1 та їхнє миттєве зчитування/модифікацію вузлом №2 без Sticky Sessions.

---

## 📂 Структура проєкту `visual_inspiration_boards`

| Шлях | Призначення |
|---|---|
| [`app/main.py`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/main.py) | Точка входу FastAPI: CORS, middleware `X-Instance-ID`, статичні файли, обробка помилок. |
| [`app/api/v1/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/api/v1/) | Маршрутизатори REST API (`boards`, `elements`, `collaborators`, `users`, `health`). |
| [`app/models/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/models/) | ORM моделі SQLAlchemy (`User`, `Board`, `CanvasElement` з JSONB, `BoardCollaborator`). |
| [`app/schemas/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/schemas/) | DTO схеми Pydantic v2 (строга валідація, `HealthResponse` з `instance_id`). |
| [`app/services/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/services/) | Бізнес-логіка: сервіси дощок, пакетні операції (batch), автоініціалізація та demo-дані. |
| [`app/core/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/core/) | Базова конфігурація: підключення до БД, клієнт Redis, `INSTANCE_ID`. |
| [`app/static/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/static/) | Фронтенд: Tiffany UI, 2D-канвас, гострі кути, бейдж активного вузла. |
| [`docker/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/docker/) | `Dockerfile` та `nginx/nginx.conf` (Round-Robin для 2 вузлів, failover). |
| [`docker-compose.yml`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/docker-compose.yml) | Декларативний запуск 2 бекенд-інстансів (`backend-1`, `backend-2`), Postgres, Redis та Nginx. |
| [`tests/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/tests/) | Інтеграційні тести API (`test_api.py`) та тести stateless стійкості (`test_stateless_resilience.py`). |
| [`scripts/verify_cluster.py`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/scripts/verify_cluster.py) | Скрипт live-демонстрації Round-Robin та Cross-Instance узгодженості для захисту роботи. |
| [`REPORT_LAB1.md`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/REPORT_LAB1.md) | Звіт з Лабораторної роботи №1 (System Design & MVP). |
| [`REPORT_LAB2.md`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/REPORT_LAB2.md) | **Звіт з Лабораторної роботи №2 (Stateless Architecture & Resilience).** |
