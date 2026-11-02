// Lab 5: спільна частина всіх сценаріїв — профіль навантаження та формування звіту.
export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
export const API = `${BASE_URL}/api/v1`;
export const JSON_HEADERS = { headers: { 'Content-Type': 'application/json' } };

const LEVELS = (__ENV.LEVELS || '10,25,50,100,200').split(',').map(Number); // ступені VUs
const STAGE_SEC = Number(__ENV.STAGE_SEC || 30);   // тривалість одного ступеня
const WARMUP_SEC = Number(__ENV.WARMUP_SEC || 15); // тривалість розігріву

// Staging Ramp-Up: warm-up + послідовні сценарії constant-vus (10 -> 25 -> 50 -> 100 -> 200).
// Кожен ступінь — окремий k6-scenario, тому k6 рахує метрики для нього окремо (тег scenario).
export function buildOptions() {
  const scenarios = {
    // Розігрів: ініціалізація пулів з'єднань (SQLAlchemy, Redis, keepalive), DNS, кешу. У таблицю не входить.
    warmup: { executor: 'constant-vus', vus: 5, duration: `${WARMUP_SEC}s`, gracefulStop: '0s' },
  };
  const thresholds = {};
  LEVELS.forEach((vus, i) => {
    const name = `vu_${vus}`;
    scenarios[name] = {
      executor: 'constant-vus',
      vus,
      duration: `${STAGE_SEC}s`,
      startTime: `${WARMUP_SEC + i * STAGE_SEC}s`,
      gracefulStop: '0s', // наступний ступінь не перекривається хвостом попереднього
    };
    // Порожні thresholds змушують k6 зберегти окремі sub-метрики для кожного ступеня
    thresholds[`http_reqs{scenario:${name}}`] = [];
    thresholds[`http_req_duration{scenario:${name}}`] = [];
    thresholds[`http_req_failed{scenario:${name}}`] = [];
  });
  return {
    scenarios,
    thresholds,
    summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
    discardResponseBodies: false,
  };
}

// handleSummary: таблиця "VUs | RPS | Avg | p50 | p95 | p99 | Error %" + графік (mermaid) у results/<name>.md
export function makeSummary(data) {
  const name = __ENV.NAME || 'result';
  const rows = LEVELS.map((vus) => {
    const s = `{scenario:vu_${vus}}`;
    const d = data.metrics[`http_req_duration${s}`].values;
    const reqs = data.metrics[`http_reqs${s}`].values.count;
    const failed = data.metrics[`http_req_failed${s}`].values.rate;
    return {
      vus,
      rps: reqs / STAGE_SEC, // Throughput = кількість запитів / тривалість ступеня
      avg: d.avg, p50: d.med, p95: d['p(95)'], p99: d['p(99)'],
      err: failed * 100,
    };
  });

  const f = (x) => x.toFixed(1);
  let md = `### ${name}\n\n`;
  md += '| VUs | Throughput (RPS) | Avg, ms | p50, ms | p95, ms | p99, ms | Error Rate, % |\n';
  md += '|---|---|---|---|---|---|---|\n';
  rows.forEach((r) => {
    md += `| ${r.vus} | ${f(r.rps)} | ${f(r.avg)} | ${f(r.p50)} | ${f(r.p95)} | ${f(r.p99)} | ${r.err.toFixed(2)} |\n`;
  });

  // Графіки у форматі Mermaid xychart (рендеряться GitHub-ом прямо в README)
  const x = `x-axis "VUs" [${LEVELS.join(', ')}]`;
  md += '\n```mermaid\nxychart-beta\n  title "' + name + ': Throughput, RPS"\n  ' + x +
    '\n  y-axis "RPS"\n  bar [' + rows.map((r) => f(r.rps)).join(', ') + ']\n```\n';
  md += '\n```mermaid\nxychart-beta\n  title "' + name + ': Latency p50 / p95 / p99, ms"\n  ' + x +
    '\n  y-axis "ms"\n' +
    '  line [' + rows.map((r) => f(r.p50)).join(', ') + ']\n' +
    '  line [' + rows.map((r) => f(r.p95)).join(', ') + ']\n' +
    '  line [' + rows.map((r) => f(r.p99)).join(', ') + ']\n```\n';

  return {
    stdout: '\n' + md,
    [`load-tests/results/${name}.md`]: md,
    [`load-tests/results/${name}.json`]: JSON.stringify(rows, null, 2),
  };
}
