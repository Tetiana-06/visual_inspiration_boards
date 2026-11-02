# Lab 6: Single Primary vs Primary + Replica (~5 хв).
# Запуск з кореня проєкту при піднятому стеку:
#   powershell -ExecutionPolicy Bypass -File load-tests\run_lab6.ps1
# Результати: load-tests\results\D_single.md, D_replica.md (+ .json) і lab6_env_log.txt (CPU вузлів БД)

$LOG = "load-tests\results\lab6_env_log.txt"
New-Item -ItemType Directory -Force load-tests\results | Out-Null
Set-Content $LOG "" -Encoding utf8

function Run-Test($name) {
    # Через ~75 с (ступені 100/200 VUs) у фоні знімаємо CPU контейнерів
    $stats = Start-Job { Start-Sleep 75; docker stats --no-stream --format "{{.Name}} {{.CPUPerc}} {{.MemUsage}}" }
    k6 run -e NAME=$name -e STAGE_SEC=20 load-tests\scenario_d_replica_read.js
    Add-Content $LOG "== $name docker stats @ ~vu_100/200" -Encoding utf8
    Receive-Job $stats -Wait | Add-Content $LOG -Encoding utf8
    Start-Sleep 10
}

# 1. Single Primary Topology: бекенди не використовують репліку
$env:USE_REPLICA = "false"; docker compose up -d backend-1 backend-2 backend-3; Start-Sleep 15
Run-Test "D_single"

# 2. Primary + Replica Topology: read-трафік на Replica
Remove-Item Env:USE_REPLICA; docker compose up -d backend-1 backend-2 backend-3; Start-Sleep 15
Run-Test "D_replica"

Add-Content $LOG "DONE" -Encoding utf8
