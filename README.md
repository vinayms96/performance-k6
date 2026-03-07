# performance-k6

Performance testing suite for the [Notes API](https://practice.expandtesting.com/notes/api) built with [k6](https://k6.io/) and TypeScript.

---

## Project Structure

```
performance-k6/
├── tests/
│   └── e2e.ts              # Main test — full CRUD flow on Notes API
├── config/
│   ├── options.ts          # k6 options: thresholds + active scenario
│   └── scenarios.ts        # All 6 executor scenario configs
├── helpers/
│   ├── setup.ts            # login() and healthCheckCall() used in setup()
│   └── metrics.ts          # Custom metric declarations (Counter, Trend, Rate, Gauge)
├── data/
│   ├── constants.ts        # Base URL and endpoint paths
│   ├── notes-data.ts       # Test note payloads (SharedArray data)
│   └── users.ts            # Test user accounts for login
├── .env                    # Environment variables (not committed)
└── package.json
```

---

## Prerequisites

- [k6](https://k6.io/docs/get-started/installation/) installed globally
- Node.js (for `npm install`)

---

## Setup

```bash
npm install
```

Copy `.env` and fill in values (see [Environment Variables](#environment-variables)):

```bash
cp .env.example .env
```

---

## Running Tests

```bash
npm run test
# expands to: dotenv k6 run tests/e2e.ts
```

Run with a specific scenario override:

```bash
dotenv k6 run --env VUS=5 --env ITERATIONS=10 tests/e2e.ts
```

---

## API Under Test

**Base URL:** `https://practice.expandtesting.com/notes/api`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health-check` | Service health (run in `setup()`) |
| POST | `/users/login` | Authenticate and get token (run in `setup()`) |
| GET | `/notes` | List all notes |
| POST | `/notes` | Create a note |
| PUT | `/notes/:id` | Update a note |
| PATCH | `/notes/:id` | Partial update (toggle completed) |
| DELETE | `/notes/:id` | Delete a note |

Each iteration performs the full CRUD flow: GET → CREATE → EDIT → PATCH → DELETE.

---

## Scenarios

All scenarios are defined in `config/scenarios.ts` and configured via environment variables. Switch between them by updating the active scenario in `config/options.ts`.

| Scenario | Executor | When to use |
|----------|----------|-------------|
| `sharedIterations` | `shared-iterations` | Fixed total iterations split across VUs — best for measuring throughput |
| `perVUIterations` | `per-vu-iterations` | Each VU runs the same number of iterations — useful for partitioned test data |
| `constantVUs` | `constant-vus` | Fixed VU count for a set duration — standard soak/load test |
| `rampingVUs` | `ramping-vus` | VUs ramp up and down in stages — stress/spike tests |
| `constantArrivalRate` | `constant-arrival-rate` | Fixed iteration rate (RPS) independent of response time |
| `rampingArrivalRate` | `ramping-arrival-rate` | Iteration rate ramps up/down — for gradual load increase tests |

---

## Environment Variables

Defined in `.env` and injected at runtime via `dotenv-cli`.

| Variable | Description | Example |
|----------|-------------|---------|
| `PASSWORD` | Login password for test accounts | `secret123` |
| `VUS` | Number of virtual users | `3` |
| `ITERATIONS` | Total/per-VU iterations | `3` |
| `DURATION` | Test duration (for time-based executors) | `10s` |
| `MAX_DURATION` | Max allowed duration | `10s` |
| `START_VUS` | Starting VUs for ramping scenarios | `0` |
| `GRACEFUL_RAMPDOWN` | Grace period before force-stopping VUs | `0s` |
| `RATE` | Target iteration rate (arrival rate scenarios) | `5` |
| `START_RATE` | Starting rate for ramping arrival rate | `0` |
| `TIME_UNIT` | Time window for rate (e.g. `1s` = per second) | `1s` |
| `PRE_ALLOCATED_VUS` | Pre-allocated VUs for arrival rate scenarios | `3` |
| `MAX_VUS` | Max VUs for ramping arrival rate | `3` |

---

## Custom Metrics

Declared in `helpers/metrics.ts` and recorded per HTTP method using tags.

| Metric | Type | What it tracks |
|--------|------|----------------|
| `request_count` | Counter | Total requests made per operation |
| `request_duration` | Trend | Actual response time (`timings.duration`) per operation |
| `error_rate` | Rate | Fraction of requests that returned non-200 per operation |
| `gauge_count` | Gauge | Last observed point-in-time value per operation |

All metrics are tagged with `{ request: 'GET|POST|PUT|PATCH|DELETE', resource: 'notes' }`, enabling per-operation threshold filtering and dashboard segmentation.

---

## Thresholds

Defined in `config/options.ts`.

| Metric | Threshold | Purpose |
|--------|-----------|---------|
| `http_req_duration` | `p(90/95/99) < 500ms` | Built-in latency SLO across all requests |
| `http_req_failed` | `rate < 1%` | Built-in failure rate (k6 marks non-2xx as failed) |
| `request_count{request:*}` | `count < 10` | Catches steps being skipped or over-executed |
| `request_duration{request:*}` | `p(90/95/99) < 500ms` | Per-operation latency SLO |
| `error_rate{request:*}` | `rate < 1%` | Per-operation error rate SLO |
| `gauge_count{request:*}` | `value > 0` | Confirms a value was observed for each operation |
