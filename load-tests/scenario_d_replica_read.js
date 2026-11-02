// Lab 6 — Read Scaling: тільки "eventual" читання, які бекенд маршрутизує на Replica.
// Порівнюємо дві топології (див. load-tests/run_lab6.ps1):
//   USE_REPLICA=false -> Single Primary: усі читання йдуть на Primary
//   USE_REPLICA=true  -> Primary + Replica: ці ж читання йдуть на Replica
// Запуск: k6 run -e NAME=D_single load-tests/scenario_d_replica_read.js
import http from 'k6/http';
import { check } from 'k6';
import { API, buildOptions, makeSummary } from './lib.js';

export const options = buildOptions();

export function setup() {
  const boards = http.get(`${API}/boards?limit=100`).json();
  return { ids: boards.map((b) => b.id) };
}

export default function (data) {
  const id = data.ids[Math.floor(Math.random() * data.ids.length)];
  const r = Math.random();
  let res;
  if (r < 0.6) {
    // 60%: каталог дощок (список + кількість елементів) — Eventual
    res = http.get(`${API}/boards?limit=20&skip=${Math.floor(Math.random() * 50)}`, { tags: { name: 'GET /boards' } });
  } else if (r < 0.9) {
    // 30%: експорт / звіт по дошці — Eventual
    res = http.get(`${API}/boards/${id}/export`, { tags: { name: 'GET /boards/{id}/export' } });
  } else {
    // 10%: публічний список користувачів — Eventual
    res = http.get(`${API}/users`, { tags: { name: 'GET /users' } });
  }
  check(res, { 'status 200': (x) => x.status === 200 });
}

export const handleSummary = makeSummary;
