# Звіт з Лабораторної роботи №2
**Тема:** Архітектура без стану (Stateless Application Architecture) та винесення стану системи  
**Проєкт:** Платформа інтерактивних дошок візуального натхнення (*Collaborative Moodboard Canvas Platform* — Inspiration Boards)  

---

## 1. Мета роботи
Підготувати сервісний рівень (*Application Layer*) програмного комплексу до горизонтального масштабування. Усунути залежність бізнес-логіки від локального стану конкретного процесу сервісу (*instance*) та забезпечити узгоджену, детерміновану роботу платформи при паралельному запуску кількох backend-вузлів за балансувальником навантаження без використання сесійного прилипання (*Sticky Sessions*).

---

## 2. Аудит та класифікація стану застосунку (State Audit)

У ході аналізу базового прототипу стан системи було формалізовано та розділено на три фундаментальні категорії:

```mermaid
flowchart TD
    subgraph Audit["Класифікація стану застосунку"]
        direction TB
        E["1. Ephemeral / Local Safe\n• Локальні змінні та Pydantic DTO\n• Стек викликів асинхронних корутин\n• Локальні логи процесу"]
        S["2. Shared / Externalized\n• Доменні сутності (Board, User, Elements)\n• Права доступу (Collaborators)\n• Спільний кеш знімків дощок"]
        C["3. Critical Stateful Dependencies\n(ВИЛУЧЕНО З ПАМ'ЯТІ ПРОЦЕСУ)\n• In-memory кеші та словники\n• Application-level locks (in-memory)\n• Sticky Sessions у балансувальнику\n• Локальні файли на диску контейнера"]
    end
    
    S --> DB[("PostgreSQL 16 (Primary DB)\nПерсистентні дані")]
    S --> REDIS[("Redis 7 (Key-Value Store)\nРозподілений кеш")]
```

### Деталізація категорій:

1. **Ephemeral / Local Safe (Тимчасовий / Локально безпечний стан):**
   - Змінні в межах контексту виконання конкретного HTTP-запиту (локальні змінні функцій, екземпляри схем Pydantic).
   - Локальні системні логи, що виводяться в `stdout/stderr` конкретного контейнера.
   - Метадані поточного запиту (`request.state`, заголовки).
   - *Висновок:* Безпечний для масштабування, оскільки його життєвий цикл суворо обмежений тривалістю одного запиту і він автоматично очищується збирачем сміття (GC).

2. **Shared / Externalized (Спільний / Винесений стан):**
   - **Первинні персистентні дані:** Дошки (`Board`), елементи канвасу (`CanvasElement` із координатами та JSONB-вмістом), користувачі (`User`), права доступу (`BoardCollaborator`). Зберігаються у реляційній СУБД **PostgreSQL 16**.
   - **Транзитивний стан та кеш:** Знімки дощок для прискореного читання (`board:{id}`). Зберігаються у централізованому розподіленому сховищі **Redis 7**.
   - *Висновок:* Весь спільний стан винесено у зовнішні мережеві сервіси, доступні всім вузлам бекенду одночасно.

3. **Critical Stateful Dependencies (Критичний стан, що підлягав усуненню):**
   - **In-Memory словники / локальні кеші:** Будь-які глобальні змінні або кеші в пам'яті Python-процесу призводили б до розсинхронізації (розколу стану / *state drift*), коли один екземпляр володіє свіжими даними, а інший — застарілими. Усунено: усі операції кешування та інвалідації здійснюються виключно через централізований Redis.
   - **Локальні блокування (In-Memory Locks):** Використання примітивів синхронізації `asyncio.Lock` або `threading.Lock` не захищає дані від паралельного запиту, що надійшов на інший сервер. Усунено: захист від конфліктів реалізовано через **Optimistic Concurrency Control** (версіонування `version` на рівні рядка в PostgreSQL) та транзакції СУБД.
   - **Sticky Sessions:** Прив'язка клієнтів за IP або Cookies до конкретного контейнера. Усунено: Nginx сконфігуровано на алгоритм чистого **Round-Robin** без будь-якої сесійної спорідненості.
   - **Файлові сесії / локальні асети:** Відсутність збереження файлів у локальну файлову систему контейнера; всі графічні асети оперують абсолютними URL-адресами та зберігаються як JSONB-властивості.

---

## 3. Рефакторинг та декомпозиція локального стану

Для забезпечення принципу **Stateless Application Architecture** було впроваджено наступні рішення:
- **Повна взаємозамінність вузлів (Interchangeable Workers):** Кожен запущений екземпляр бекенду (`backend-1`, `backend-2`) є повністю ідентичним та рівноправним. Жоден вузол не зберігає унікального бізнес-контексту.
- **Ідентифікація вузлів (Node Identification):** Створено FastAPI Middleware, що автоматично додає заголовок відповіді **`X-Instance-ID`** (значення береться зі змінної середовища `INSTANCE_ID` або системного hostname). Це дозволяє надійно відстежувати маршрутизацію запитів під час тестування та моніторингу.
- **Відсутність залишкових мутацій:** Після обробки запиту в пам'яті Python-процесу не залишається жодних змінених глобальних структур.

---

## 4. Специфікація Stateless Request Flow

Для ключового бізнес-сценарію — **пакетної синхронізації елементів канвасу під час перетягування (Drag-and-Drop Batch Sync)** — побудовано наскрізний потік виконання:

```mermaid
sequenceDiagram
    autonumber
    actor Client as Клієнтський браузер
    participant Nginx as Nginx (Round-Robin)
    participant Node1 as Backend Instance 1 (X-Instance-ID)
    participant Node2 as Backend Instance 2 (X-Instance-ID)
    participant DB as PostgreSQL 16 (Shared DB)
    participant Cache as Redis 7 (Shared Cache)

    Note over Client, Cache: Сценарій 1: Запис і пакетне оновлення (Instance 1)
    Client->>Nginx: POST /api/v1/boards/1/elements/batch<br/>{expected_version: 1, elements: [...]}
    Nginx->>Node1: Проксіювання запиту (Node 1)
    Node1->>DB: SELECT * FROM boards WHERE id = 1 FOR UPDATE
    DB-->>Node1: board {version: 1}
    Note over Node1: Перевірка Optimistic Lock:<br/>expected_version (1) == board.version (1) - OK
    Node1->>DB: Batch UPSERT canvas_elements<br/>UPDATE boards SET version = 2
    DB-->>Node1: Транзакція успішно зафіксована (COMMIT)
    Node1->>Cache: DEL board:1 (Інвалідація кешу)
    Cache-->>Node1: OK
    Node1-->>Nginx: HTTP 200 OK + Header [X-Instance-ID: backend-instance-1]
    Nginx-->>Client: HTTP 200 OK + Header [X-Instance-ID: backend-instance-1]

    Note over Client, Cache: Сценарій 2: Послідовне читання іншим вузлом (Instance 2)
    Client->>Nginx: GET /api/v1/boards/1
    Nginx->>Node2: Проксіювання запиту (Round-Robin -> Node 2)
    Node2->>Cache: GET board:1
    Cache-->>Node2: Cache MISS (раніше інвалідовано Node 1)
    Node2->>DB: SELECT * FROM boards WHERE id = 1 (включаючи elements)
    DB-->>Node2: Fresh Board Data (version: 2, оновлені координати)
    Node2->>Cache: SET board:1 (оновлення кешу на 300с)
    Node2-->>Nginx: HTTP 200 OK + Header [X-Instance-ID: backend-instance-2]
    Nginx-->>Client: HTTP 200 OK + Header [X-Instance-ID: backend-instance-2]
```

### Фіксація параметрів потоку:
1. **Вхідні параметри:** Тіло запиту DTO `BatchCanvasElementUpdate`, `expected_board_version: 1`, список елементів.
2. **Вичитування контексту:** Зі спільного сховища (PostgreSQL) перевіряється актуальний стан версії дошки.
3. **Атомарна зміна стану:** Пакетне збереження координат елементів та інкремент версії `version = 2` в одній транзакції PostgreSQL.
4. **Інвалідація розподіленого кешу:** Очищення ключа `board:1` у спільному Redis.
5. **Завершення запиту:** Повернення клієнту заголовка `X-Instance-ID: backend-instance-1`. У пам'яті вузла `Node 1` не залишається жодних залишкових даних.

---

## 5. Мульти-екземплярне розгортання та ідентифікація

Конфігурація середовища розгортання в [`docker-compose.yml`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/docker-compose.yml) містить два повноцінні незалежні екземпляри бекенду:

```yaml
services:
  backend-1:
    build: { context: ., dockerfile: docker/Dockerfile }
    container_name: vib_backend_1
    environment:
      - INSTANCE_ID=backend-instance-1
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/visual_boards
      - REDIS_URL=redis://redis:6379/0

  backend-2:
    build: { context: ., dockerfile: docker/Dockerfile }
    container_name: vib_backend_2
    environment:
      - INSTANCE_ID=backend-instance-2
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/visual_boards
      - REDIS_URL=redis://redis:6379/0
```

Конфігурація балансувальника у [`docker/nginx/nginx.conf`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/docker/nginx/nginx.conf):
```nginx
upstream backend_cluster {
    server backend-1:8000 max_fails=3 fail_timeout=5s;
    server backend-2:8000 max_fails=3 fail_timeout=5s;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend_cluster;
        proxy_pass_header X-Instance-ID;
        proxy_next_upstream error timeout http_502 http_503 http_504;
    }
}
```

---

## 6. Моделювання збоїв та тестування консистентності (Resilience Testing)

У проєкті реалізовано автоматизований набір тестів у [`tests/test_stateless_resilience.py`](file:///C:/Users/Tetiana/PycharmProjects/visual_inspiration_boards/tests/test_stateless_resilience.py):

### 6.1. Тест Cross-Instance Consistency (Міжвузлова узгодженість)
- **Крок 1:** `POST /api/v1/boards` надсилається на `backend-instance-1`. Створюється дошка з `version = 1`. Заголовок відповіді: `X-Instance-ID: backend-instance-1`.
- **Крок 2:** `GET /api/v1/boards/{id}` надсилається на `backend-instance-2`. Вузол 2 негайно повертає створену дошку з актуальними даними. Заголовок: `X-Instance-ID: backend-instance-2`.
- **Крок 3:** `POST /api/v1/boards/{id}/elements/batch` надсилається на `backend-instance-2`. Додаються нові елементи, версія стає `version = 2`.
- **Крок 4:** `GET /api/v1/boards/{id}` надсилається назад на `backend-instance-1`. Вузол 1 негайно зчитує нову версію `version = 2` та всі додані елементи без затримок чи розбіжностей.
- **Результат:** ✅ `PASSED` — відсутність Sticky Sessions не призводить до розсинхронізації даних.

### 6.2. Тест Restart / Instance Loss Scenario (Аварійна зупинка вузла)
- **Сценарій:** Вузол `backend-1` створює дані та раптово аварійно завершує роботу (`simulated crash / docker stop`).
- **Поведінка системи:** Усі наступні запити на читання, зміну та експорт обробляються вузлом `backend-2`.
- **Результат:** ✅ `PASSED` — втрата вузла не спричиняє втрати жодного байту бізнес-даних, оскільки весь стан збережено у зовнішній базі даних.

Результати проходження повного набору тестів:
```text
tests/test_api.py::test_health_check PASSED                              [ 14%]
tests/test_api.py::test_get_users PASSED                                 [ 28%]
tests/test_api.py::test_boards_crud_and_optimistic_locking PASSED        [ 42%]
tests/test_api.py::test_collaborators_management PASSED                  [ 57%]
tests/test_stateless_resilience.py::test_instance_identification_header PASSED [ 71%]
tests/test_stateless_resilience.py::test_cross_instance_consistency PASSED [ 85%]
tests/test_stateless_resilience.py::test_instance_loss_and_recovery PASSED [100%]

============================== 7 passed in 1.08s ==============================
```

---

## 7. Актуалізована архітектурна схема (C4 Model: Container Level)

```mermaid
flowchart TD
    subgraph Clients["Клієнтський шар"]
        Browser["Веб-браузер (Aesthetic Tiffany UI)\nВізуальний бейдж активного вузла (node: ...)"]
    end

    subgraph Edge["Балансувальник та проксі"]
        Nginx["Nginx Reverse Proxy (Round-Robin)\nПорт 80 / 8080\nproxy_pass_header X-Instance-ID\nАвто-failover: proxy_next_upstream"]
    end

    subgraph StatelessApplicationLayer["Сервісний шар без стану (Stateless Cluster)"]
        Node1["Backend Node 1 (FastAPI)\nINSTANCE_ID: backend-instance-1\nПорт 8000\nInterchangeable Worker"]
        Node2["Backend Node 2 (FastAPI)\nINSTANCE_ID: backend-instance-2\nПорт 8000\nInterchangeable Worker"]
    end

    subgraph SharedDataLayer["Спільний рівень стану (Externalized State)"]
        Postgres[("PostgreSQL 16 (Primary DB)\nТранзакції + Optimistic Locking\nPersistent Volume: postgres_data")]
        Redis[("Redis 7 (Distributed Cache)\nЦентралізований кеш знімків дощок\nPersistent Volume: redis_data")]
    end

    Browser -- "HTTP / REST (JSON)" --> Nginx
    Nginx -- "Round-Robin Запит #1, #3" --> Node1
    Nginx -- "Round-Robin Запит #2, #4" --> Node2

    Node1 -- "SQLAlchemy Async (asyncpg)" --> Postgres
    Node1 -- "aioredis (Shared Cache)" --> Redis

    Node2 -- "SQLAlchemy Async (asyncpg)" --> Postgres
    Node2 -- "aioredis (Shared Cache)" --> Redis

    Node1 -. "Response [X-Instance-ID: backend-instance-1]" .-> Nginx
    Node2 -. "Response [X-Instance-ID: backend-instance-2]" .-> Nginx
    Nginx -. "Response [X-Instance-ID]" .-> Browser
```

---

## 8. Інструкція для захисту та Live-демонстрації

### Крок 1. Запуск кластера з двома екземплярами:
```bash
docker compose up --build -d
```

### Крок 2. Автоматизована live-демонстрація балансування та консистентності:
Запустіть спеціальний скрипт демонстрації:
```bash
python scripts/verify_cluster.py http://localhost:8080
```
Скрипт у реальному часі виведе:
1. Почергове чергування відповідей: `backend-instance-1` → `backend-instance-2` (Round-Robin).
2. Створення дошки на одному вузлі та її миттєве прочитання іншим вузлом.

### Крок 3. Live-демонстрація збою (Instance Loss Scenario):
1. В окремому терміналі зупиніть перший вузол:
   ```bash
   docker stop vib_backend_1
   ```
2. Повторно виконайте запити у браузері або через скрипт:
   ```bash
   python scripts/verify_cluster.py http://localhost:8080
   ```
3. **Результат:** Nginx миттєво перенаправляє всі запити на `backend-instance-2`, жодної помилки 502/504 немає, всі раніше створені дошки та стікери цілісні.

---

## 9. Висновки
У ході виконання Лабораторної роботи №2:
1. Проведено аудит стану системи: повністю вилучено залежність від локальної пам'яті процесу (`in-memory state`, локальні блокування).
2. Весь бізнес-стан винесено у зовнішні розподілені сховища — **PostgreSQL 16** (персистентність і транзакції) та **Redis 7** (розподілений кеш).
3. Розгорнуто мульти-екземплярний кластер із двох паралельних вузлів (`backend-1`, `backend-2`) за балансувальником Nginx із круговим розподілом навантаження (*Round-Robin*).
4. Реалізовано ідентифікацію вузлів через HTTP-заголовок **`X-Instance-ID`** та інтегровано його відображення у веб-інтерфейс.
5. Експериментально підтверджено відсутність втрати даних та збереження цілісності при почерговому опрацюванні запитів різними вузлами і при аварійній зупинці одного з них.
