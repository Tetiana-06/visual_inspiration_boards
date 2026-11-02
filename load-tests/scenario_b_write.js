// Scenario B — Write-Intensive: користувачі додають і переміщують елементи на спільних дошках.
// Ресурсний профіль: INSERT/UPDATE у PostgreSQL (WAL, commit, row locks), інвалідація кешу.
// Запуск: k6 run -e NAME=B_write load-tests/scenario_b_write.js
import http from 'k6/http';
import { check } from 'k6';
import { API, JSON_HEADERS, buildOptions, makeSummary } from './lib.js';

export const options = buildOptions();

const BOARDS = 5; // кілька спільних дощок => конкуренція записів за ті самі рядки/індекси

export function setup() {
  const ids = [];
  for (let i = 0; i < BOARDS; i++) {
    const res = http.post(`${API}/boards`, JSON.stringify({ title: `k6 write board ${i}` }), JSON_HEADERS);
    ids.push(res.json().id);
  }
  return { ids };
}

export default function (data) {
  const boardId = data.ids[Math.floor(Math.random() * data.ids.length)];
  // 1. Створення нового елемента (INSERT)
  const created = http.post(
    `${API}/boards/${boardId}/elements`,
    JSON.stringify({ element_type: 'note', x: Math.random() * 2000, y: Math.random() * 1200, content: { text: 'k6' } }),
    Object.assign({ tags: { name: 'POST /elements' } }, JSON_HEADERS),
  );
  if (!check(created, { 'element 201': (r) => r.status === 201 })) return;

  // 2. Переміщення цього елемента (UPDATE)
  const moved = http.put(
    `${API}/boards/${boardId}/elements/${created.json().id}`,
    JSON.stringify({ x: Math.random() * 2000, y: Math.random() * 1200 }),
    Object.assign({ tags: { name: 'PUT /elements/{id}' } }, JSON_HEADERS),
  );
  check(moved, { 'element moved 200': (r) => r.status === 200 });
}

// Прибирання: видалення тестових дощок (елементи видаляються каскадно)
export function teardown(data) {
  data.ids.forEach((id) => http.del(`${API}/boards/${id}`));
}

export const handleSummary = makeSummary;
