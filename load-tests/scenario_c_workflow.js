// Scenario C — Complex Workflow: повний життєвий цикл дошки одним користувачем.
// create board -> 3 elements -> GET (MISS, потім HIT) -> PATCH з optimistic lock -> export -> delete.
// Ресурсний профіль: змішані read/write, транзакції, серіалізація великого JSON (export), інвалідація кешу.
// Запуск: k6 run -e NAME=C_workflow load-tests/scenario_c_workflow.js
import http from 'k6/http';
import { check } from 'k6';
import { API, JSON_HEADERS, buildOptions, makeSummary } from './lib.js';

export const options = buildOptions();

export default function () {
  const board = http.post(`${API}/boards`, JSON.stringify({ title: 'k6 workflow' }),
    Object.assign({ tags: { name: 'POST /boards' } }, JSON_HEADERS));
  if (!check(board, { 'board 201': (r) => r.status === 201 })) return;
  const id = board.json().id;

  for (let i = 0; i < 3; i++) {
    http.post(`${API}/boards/${id}/elements`,
      JSON.stringify({ element_type: 'note', x: i * 300, y: 100, content: { text: `note ${i}` } }),
      Object.assign({ tags: { name: 'POST /elements' } }, JSON_HEADERS));
  }

  const detail = http.get(`${API}/boards/${id}`, { tags: { name: 'GET /boards/{id}' } }); // MISS -> БД
  http.get(`${API}/boards/${id}`, { tags: { name: 'GET /boards/{id}' } });                // HIT -> Redis

  const patched = http.patch(`${API}/boards/${id}`,
    JSON.stringify({ description: 'edited by k6', expected_version: detail.json().version }),
    Object.assign({ tags: { name: 'PATCH /boards/{id}' } }, JSON_HEADERS));
  check(patched, { 'patch 200': (r) => r.status === 200 });

  http.get(`${API}/boards/${id}/export`, { tags: { name: 'GET /export' } });
  http.del(`${API}/boards/${id}`, null, { tags: { name: 'DELETE /boards/{id}' } });
}

export const handleSummary = makeSummary;
