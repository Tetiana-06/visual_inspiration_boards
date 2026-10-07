# 📌 Visual Inspiration Boards (Collaborative Moodboard Platform)

> **Лабораторна робота № 1**: Проєктування архітектури (System Design) та реалізація базового прототипу розподіленої/модульної системи (MVP / Architectural Baseline).  
> **Естетика та інтерфейс:** Pinterest Vibe — теплі органічні відтінки, стікери-нотатки, кольорові палітри, інтерактивний 2D-канвас із підтримкою drag-and-drop та пакетної синхронізації.

---

## 🎨 Особливості платформи
- **Pinterest Aesthetic UI:**
  - Тепла палітра кольорів (`Warm Linen #FAF8F5`, `Blush Terracotta`, `Sage Mist`).
  - Візуальні елементи канвасу: естетичні фотокартки, текстурні стікери із загнутими краями, палітри кольорів із 5 зразками (копіювання HEX в один клік), цитати-стікери.
  - Інтерактивне переміщення мишкою (Drag-and-Drop) по 2D полотну.
  - Пакетна синхронізація (`Batch Sync`) для оптимізації кількості мережевих запитів.
- **System Design & Архітектура:**
  - **Stateless Backend:** FastAPI (Python 3.12+), асинхронна архітектура на базі Uvicorn.
  - **Optimistic Concurrency Control:** поле `version` у дошці запобігає перезапису правок іншими користувачами (повертає `HTTP 409 Conflict` у разі конфлікту).
  - **Persistence Layer:** PostgreSQL 16 (з підтримкою `JSONB` для довільних властивостей елементів) + збереження даних на диск через Docker Volume (`postgres_data`).
  - **Кешування:** Redis 7 для швидкого збереження знімків дощок та зниження навантаження на первинну СУБД.
  - **Балансування:** Nginx як зворотний проксі (Reverse Proxy), стиснення gzip, роздача статики.
  - **Автоматичне наповнення даними:** при першому запуску автоматично створюються естетичні демо-дошки (*"Wabi-Sabi & Japandi Interior"*, *"Autumn Warmth & Editorial Capsule"*).

---

## 🚀 Як запустити проєкт

### Варіант 1: Запуск через Docker Compose (Рекомендовано для здачі лабораторної)
Усе середовище (Nginx + Backend + PostgreSQL + Redis) піднімається **однією командою**:

```bash
docker compose up --build -d
```

Після запуску відкрийте у браузері:
- **Веб-інтерфейс (Pinterest UI):** [http://localhost](http://localhost) або [http://localhost:8080](http://localhost:8080)
- **Інтерактивна документація OpenAPI / Swagger:** [http://localhost/docs](http://localhost/docs)
- **Health Check системи:** [http://localhost/api/v1/health](http://localhost/api/v1/health)

Зупинити стек із збереженням даних:
```bash
docker compose down
```

---

### Варіант 2: Локальний запуск (через Python Virtualenv)
Для швидкого запуску без підняття Docker сервіс автоматично використовує локальну SQLite базу даних або локальний PostgreSQL:

1. **Активуйте віртуальне оточення та встановіть залежності:**
   ```bash
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Запустіть застосунок:**
   ```bash
   python main.py
   ```
   або через uvicorn:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Відкрийте у браузері:**
   - Веб-інтерфейс: [http://localhost:8000](http://localhost:8000)
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Запуск автоматизованих тестів
У проєкті реалізовано набір тестів (`pytest` + `httpx`), які перевіряють CRUD-операції, валідацію, пакетну синхронізацію та поведінку Optimistic Locking:

```bash
.\.venv\Scripts\pytest -v
```

---

## 📂 Структура проєкту `visual_inspiration_boards`

| Шлях | Призначення |
|---|---|
| [`app/main.py`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/main.py) | Точка входу FastAPI: конфігурація CORS, підключення роутів, static files, lifecycle hooks. |
| [`app/api/v1/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/api/v1/) | Маршрутизатори REST API (`boards`, `elements`, `collaborators`, `users`, `health`). |
| [`app/models/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/models/) | ORM моделі SQLAlchemy (`User`, `Board`, `CanvasElement` з JSONB, `BoardCollaborator`). |
| [`app/schemas/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/schemas/) | DTO схеми Pydantic v2 (строга типізація запитів і відповідей). |
| [`app/services/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/services/) | Бізнес-логіка: сервіси дощок, пакетні операції (batch), автоініціалізація та seed-дані. |
| [`app/core/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/core/) | Базова конфігурація: підключення до БД (Postgres/SQLite), клієнт Redis, доменні винятки. |
| [`app/static/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/app/static/) | Фронтенд (Pinterest UI): `index.html`, стилі `css/style.css`, логіка 2D-канвасу `js/app.js`. |
| [`docker/`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/docker/) | `Dockerfile` (багатоетапна збірка бекенду) та конфігурація `nginx/nginx.conf`. |
| [`docker-compose.yml`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/docker-compose.yml) | Декларативне розгортання всього стеку однією командою. |
| [`tests/test_api.py`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/tests/test_api.py) | Автоматичні інтеграційні тести API. |
| [`REPORT_LAB1.md`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/REPORT_LAB1.md) | **Офіційний звіт до Лабораторної роботи №1** з C4-діаграмою, описом сутностей, Bottleneck Analysis. |

---

## 📑 Детальний звіт
Повний текст звіту з C4-діаграмою контейнерів, детальним описом пікового навантаження (High-Load Scenario), специфікацією 12+ ендпоінтів та аналізом 3 вузьких місць системи доступний у файлі [`REPORT_LAB1.md`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/REPORT_LAB1.md).
