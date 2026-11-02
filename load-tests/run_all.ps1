# Lab 5: повна серія навантажувальних тестів (~15 хв).
# Запуск з кореня проєкту при піднятому стеку (docker compose up --build -d):
#   powershell -ExecutionPolicy Bypass -File load-tests\run_all.ps1
# Результати: load-tests\results\<NAME>.md (таблиця + графіки), <NAME>.json, env_log.txt (CPU/RAM, з'єднання БД, транзакції БД)

$LOG = "load-tests\results\env_log.txt"
New-Item -ItemType Directory -Force load-tests\results | Out-Null
Set-Content $LOG "" -Encoding utf8

# Кількість транзакцій PostgreSQL (для оцінки навантаження на БД)
function Get-DbXact {
    [int64](docker exec database_primary psql -U postgres -d visual_boards -tAc "select xact_commit+xact_rollback from pg_stat_database where datname='visual_boards'")
}

function Run-Test($name, $script) {
    docker exec vib_redis redis-cli FLUSHALL | Out-Null   # кожен тест стартує з порожнього кешу
    $before = Get-DbXact
    # Через 130 с (ступені 100/200 VUs) у фоні знімаємо завантаження контейнерів
    $stats = Start-Job { Start-Sleep 130; docker stats --no-stream --format "{{.Name}} {{.CPUPerc}} {{.MemUsage}}" }
    k6 run -e NAME=$name "load-tests\$script"
    Add-Content $LOG "== $name docker stats @ ~vu_100/200" -Encoding utf8
    Receive-Job $stats -Wait | Add-Content $LOG -Encoding utf8
    Add-Content $LOG "== $name DB transactions: $((Get-DbXact) - $before)" -Encoding utf8
    Start-Sleep 10   # пауза між тестами, щоб система "охолола"
}

# 1. Три сценарії на 3 інстансах з кешем
Run-Test "A_read_3inst"     "scenario_a_read.js"
Run-Test "B_write_3inst"    "scenario_b_write.js"
Run-Test "C_workflow_3inst" "scenario_c_workflow.js"

# 2. Scaling Impact: 1 інстанс
docker compose stop backend-2 backend-3; Start-Sleep 10
Run-Test "A_read_1inst" "scenario_a_read.js"
docker compose start backend-2 backend-3; Start-Sleep 5

# 3. Caching Impact: кеш вимкнено на всіх інстансах
$env:REDIS_ENABLED = "false"; docker compose up -d backend-1 backend-2 backend-3; Start-Sleep 15
Run-Test "A_read_3inst_nocache" "scenario_a_read.js"
Remove-Item Env:REDIS_ENABLED; docker compose up -d backend-1 backend-2 backend-3   # повертаємо кеш

Add-Content $LOG "DONE" -Encoding utf8
