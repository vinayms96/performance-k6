# performance-k6

Performance testing suite for the [Notes API](https://practice.expandtesting.com/notes/api) built with [k6](https://k6.io/) and TypeScript.

---

## Project Structure

```
performance-k6/
├── generate.py             # Unified AI entry point — run from project root
├── tests/
│   └── e2e.ts              # Main test — full CRUD flow on Notes API
├── config/
│   ├── options.ts          # k6 options: thresholds + active scenario
│   └── scenarios.ts        # All 6 executor scenario configs (all values from .env)
├── helpers/
│   ├── setup.ts            # login() and healthCheckCall() used in setup()
│   └── metrics.ts          # Custom metric declarations (Counter, Trend, Rate, Gauge)
├── data/
│   ├── constants.ts        # Base URL and endpoint paths
│   ├── notes-data.ts       # Test note payloads (SharedArray data)
│   └── users.ts            # Test user accounts for login
├── prompts/
│   ├── framework-context.md  # AI context: framework structure, import paths, conventions
│   └── request.prompt.md     # User-editable: describe what to test, AI generates the script
├── ai-playground/
│   ├── requirements.txt    # Python deps: anthropic + openai + python-dotenv
│   ├── .venv/              # Shared virtual environment
│   ├── openai/
│   │   ├── openai-script.py  # OpenAI entry point (gpt-5.1, Responses API)
│   │   └── shell_runner.py   # Agentic loop + guards for OpenAI
│   └── claude/
│       ├── claude-script.py  # Claude entry point (claude-opus-4-6, Messages API)
│       └── tool_runner.py    # Agentic loop + guards for Claude
├── ai-performance/         # AI-generated output (gitignored) — never edit manually
│   ├── data/               # Only created if custom API needs different constants/payloads
│   ├── helpers/            # Only created if custom API needs different auth logic
│   ├── config/             # Only created if custom API needs different thresholds
│   └── tests/              # Generated test scripts
├── .env                    # Environment variables (not committed)
└── package.json
```

---

## Prerequisites

- [k6](https://k6.io/docs/get-started/installation/) installed globally
- Node.js (for `npm install`)
- Python 3.x (for AI script generation)

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

Each scenario object uses `executor: '...' as const` to preserve the literal type required by k6's `Options` type — without it TypeScript widens the value to `string` and the type check fails.

| Scenario | Executor | When to use |
|----------|----------|-------------|
| `sharedIterations` | `shared-iterations` | Fixed total iterations split across VUs — best for measuring throughput |
| `perVUIterations` | `per-vu-iterations` | Each VU runs the same number of iterations — useful for partitioned test data |
| `constantVUs` | `constant-vus` | Fixed VU count for a set duration — standard soak/load test |
| `rampingVUs` | `ramping-vus` | VUs ramp up/down across 3 stages — stress/spike tests |
| `constantArrivalRate` | `constant-arrival-rate` | Fixed iteration rate (RPS) independent of response time |
| `rampingArrivalRate` | `ramping-arrival-rate` | Iteration rate ramps up/down across 3 stages — gradual load increase |

`rampingVUs` and `rampingArrivalRate` use 3 configurable stages driven by `STAGE_DURATION_*` and `STAGE_TARGET_*` env vars (see [Environment Variables](#environment-variables)).

---

## Environment Variables

Defined in `.env` and injected at runtime via `dotenv-cli`.

| Variable | Used by | Description | Example |
|----------|---------|-------------|---------|
| `PASSWORD` | setup | Login password for test accounts | `secret123` |
| `VUS` | constantVUs, sharedIterations, perVUIterations | Number of virtual users | `3` |
| `ITERATIONS` | sharedIterations, perVUIterations | Total or per-VU iterations | `3` |
| `DURATION` | constantVUs, constantArrivalRate | Test duration | `10s` |
| `MAX_DURATION` | sharedIterations, perVUIterations | Hard time ceiling | `10s` |
| `START_VUS` | rampingVUs | VU count before first ramp stage | `0` |
| `GRACEFUL_RAMPDOWN` | rampingVUs | Grace period before force-stopping VUs | `0s` |
| `STAGE_DURATION_1` | rampingVUs, rampingArrivalRate | Duration of stage 1 | `10s` |
| `STAGE_TARGET_1` | rampingVUs, rampingArrivalRate | Target VUs (or RPS) at end of stage 1 | `5` |
| `STAGE_DURATION_2` | rampingVUs, rampingArrivalRate | Duration of stage 2 | `20s` |
| `STAGE_TARGET_2` | rampingVUs, rampingArrivalRate | Target VUs (or RPS) at end of stage 2 | `10` |
| `STAGE_DURATION_3` | rampingVUs, rampingArrivalRate | Duration of stage 3 | `10s` |
| `STAGE_TARGET_3` | rampingVUs, rampingArrivalRate | Target VUs (or RPS) at end of stage 3 | `0` |
| `RATE` | constantArrivalRate | Target iteration rate per `TIME_UNIT` | `5` |
| `START_RATE` | rampingArrivalRate | Starting rate before ramp | `0` |
| `TIME_UNIT` | constantArrivalRate, rampingArrivalRate | Time window for rate (e.g. `1s` = per second) | `1s` |
| `PRE_ALLOCATED_VUS` | constantArrivalRate, rampingArrivalRate | Pre-allocated VUs | `3` |
| `MAX_VUS` | constantArrivalRate, rampingArrivalRate | Upper VU ceiling | `3` |

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

Defined in `config/options.ts`. Choose the threshold type based on what you want to assert:

| Type | Syntax | When to use |
|------|--------|-------------|
| **Counter** | `count < N` | Verify total requests made; catches skipped/over-executed steps. Avoid with `rampingVUs` at high concurrency — inflated totals will breach fixed limits. |
| **Trend** | `p(90/95/99) < Nms` | Enforce latency SLOs per operation. Always include in load, stress, and soak tests. |
| **Rate** | `rate < 0.01` | Fail the test if error frequency exceeds a threshold. Always pair with Trend thresholds. |
| **Gauge** | `value > N` / `value < N` | Assert the last observed point-in-time value (e.g. note count, response size). Not an aggregate. |

Active thresholds:

| Metric | Threshold | Purpose |
|--------|-----------|---------|
| `http_req_duration` | `p(90/95/99) < 400ms` | Built-in latency SLO across all requests |
| `http_req_failed` | `rate < 1%` | Built-in failure rate (k6 marks non-2xx as failed) |
| `request_count{request:*}` | `count < 10` | Catches steps being skipped or over-executed |
| `request_duration{request:*}` | `p(90/95/99) < 400ms` | Per-operation latency SLO |
| `error_rate{request:*}` | `rate < 1%` | Per-operation error rate SLO |
| `gauge_count{request:*}` | `value > 0` | Confirms a value was observed for each operation |

---

## AI Playground

`ai-playground/` contains an AI agent that generates k6 test scripts from a plain-text description.
Two AI backends are supported: **Claude** (default) and **OpenAI**.

### Setup (one time)

```bash
python -m venv ai-playground/.venv
ai-playground/.venv/bin/pip install -r ai-playground/requirements.txt
```

Add API keys to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### How it works

1. Edit `prompts/request.prompt.md` — fill in the USER FORM: api_type, scenario, load parameters, performance targets, test flow
2. Run from the project root:
   ```bash
   python3 generate.py              # defaults to Claude
   python3 generate.py --ai claude
   python3 generate.py --ai openai
   ```
3. The AI reads `prompts/framework-context.md` (framework rules) and `prompts/request.prompt.md` (your request), explores the framework files via shell commands, and writes generated test(s) into `ai-performance/`
4. Run the printed command from the project root:
   ```bash
   npm run ai:test
   # expands to: webpack && dotenv k6 run dist/<name>.js
   ```

### AI backends

| | Claude | OpenAI |
|---|---|---|
| Model | `claude-sonnet-4-6` | `gpt-5.1` |
| Entry point | `ai-playground/claude/claude-script.py` | `ai-playground/openai/openai-script.py` |
| Extras | Adaptive thinking, prompt caching | — |

Both backends share identical rules, guards, and output behaviour — only the API differs.

### api_type options

| Value | What gets generated |
|-------|---------------------|
| `framework` | Only `ai-performance/tests/<name>.ts` — reuses all framework files via `../../` imports |
| `custom` | `ai-performance/data/constants.ts` + test script, plus any files that differ from the framework (custom auth, custom thresholds, custom data) |

For `custom`, `helpers/metrics.ts` and `config/scenarios.ts` are always reused via `../../` imports — never duplicated.

`config/options.ts` behaviour differs by type:
- **framework** — spreads from the framework `config/options.ts` and overrides only what differs
- **custom** — always self-contained; never spreads from the framework because the framework's options contain Notes-API-specific Trend thresholds that don't exist in other tests and would cause a `no metric name found` runtime error

Only thresholds for HTTP methods actually used in the generated test are included. Named Trend thresholds (`per_operation_thresholds`) are only added when explicitly requested — never invented by the AI.

### Guards

The agentic loop enforces three safety guards on every run:

| Guard | When | What it does |
|-------|------|--------------|
| Framework write protection | During generation | Detects and reverts any writes to `data/`, `helpers/`, `config/`, `tests/` |
| Stray file protection | During generation | Removes files written to the wrong directory and re-prompts |
| Hardcoding violation scanner | After generation | Scans all generated `.ts` files for hardcoded VUs, duration, URLs, or credentials; re-prompts to fix |
| Text-as-code | After generation | Detects if the model returned code as text instead of writing to disk; re-prompts with path and heredoc rules |
