// Scenario A — Read-Intensive: перегляд дощок (деталі дошки через Redis Cache-Aside + список дощок з БД).
// Запуск: k6 run -e NAME=A_read load-tests/scenario_a_read.js
import http from 'k6/http';
import { check } from 'k6';
import { API, buildOptions, makeSummary } from './lib.js';

export const options = buildOptions();

// setup виконується один раз: беремо id існуючих дощок
export function setup() {
  const boards = http.get(`${API}/boards?limit=100`).json();
  return { ids: boards.map((b) => b.id) };
}

export default function (data) {
  const id = data.ids[Math.floor(Math.random() * data.ids.length)];
  if (Math.random() < 0.8) {
    // 80%: деталі дошки — кешований ендпоінт (X-Cache: HIT/MISS)
    const res = http.get(`${API}/boards/${id}`, { tags: { name: 'GET /boards/{id}' } });
    check(res, { 'board 200': (r) => r.status === 200 });
  } else {
    // 20%: список дощок — завжди БД (агрегація elements_count)
    const res = http.get(`${API}/boards?limit=20`, { tags: { name: 'GET /boards' } });
    check(res, { 'list 200': (r) => r.status === 200 });
  }
  // без sleep: closed model — кожен VU шле наступний запит одразу після відповіді
}

export const handleSummary = makeSummary;
