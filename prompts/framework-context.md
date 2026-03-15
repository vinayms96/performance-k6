# Framework Context
# This file describes the k6 performance testing framework structure.
# It is read by the AI tool to understand import paths, patterns, and conventions.
# Edit this file only if the framework structure changes (new files, moved paths, etc.).

---

## Working Directory
All shell commands run from: ai-playground/claude/ (or ai-playground/openai/)
The shell is already set to this directory — NEVER prefix commands with `cd ai-playground &&`.
Use ../../ paths directly (e.g. `cat ../../tests/e2e.ts`, `mkdir -p ../../ai-performance/tests`).


## FRAMEWORK FILE PROTECTION — Read this first

The framework source files listed below are READ-ONLY. The AI must NEVER create, overwrite,
or modify any of them. They exist only as references to read and reuse.

Read-only framework files (relative to ai-playground/claude/ or ai-playground/openai/):
  ../../data/constants.ts
  ../../data/notes-data.ts
  ../../data/users.ts
  ../../helpers/setup.ts
  ../../helpers/metrics.ts
  ../../config/scenarios.ts
  ../../config/options.ts
  ../../tests/e2e.ts
  ../../README.md

The ONE exception: ../../.env may have its existing values updated via `sed -i`.
Never add new keys, remove existing keys, or touch PASSWORD or ANTHROPIC_API_KEY or OPENAI_API_KEY.

RESTRICTED WRITE (append-only — never remove or modify existing content):
  ../../webpack.config.js  — add a new entry inside the `entry: {}` block only
  ../../package.json       — add a new script inside the `"scripts": {}` block only

ALL generated files go inside: ../../ai-performance/
No file may be written anywhere outside ../../ai-performance/ (except ../../.env edits and the two restricted-write files above).


## Folder Paths (relative to ai-playground/claude/ or ai-playground/openai/)
- FRAMEWORK='../..'                     # performance-k6 root (read-only source)
- ENV_FILE='../../.env'                 # runtime env vars — values updatable via sed
- CONFIG='../../config/'                # read-only: scenarios.ts, options.ts
- DATA='../../data/'                    # read-only: constants.ts, notes-data.ts, users.ts
- HELPERS='../../helpers/'              # read-only: setup.ts, metrics.ts
- TESTS='../../tests/'                  # read-only: hand-crafted reference tests
- OUTPUT='../../ai-performance/'        # WRITE destination — all generated output goes here


## Case A — Framework API (api_type: framework)

Use when the test targets the Notes API (practice.expandtesting.com/notes/api).

What to generate:
  ONLY: ../../ai-performance/tests/<descriptive-name>.ts

The test script imports directly from the framework source via ../../ paths:

```typescript
import { urls }                                     from '../../data/constants'
import { notes }                                    from '../../data/notes-data'
import { login, healthCheckCall }                   from '../../helpers/setup'
import { requestDuration, requestCount, errorRate, gauge } from '../../helpers/metrics'
import { customOptions }                            from '../../config/options'
import { <scenarioName> }                           from '../../config/scenarios'
```

Steps:
1. Read ../../README.md and ../../tests/e2e.ts — internalize patterns (imports, check() names, metric tags, group() blocks).
2. Read ../../data/constants.ts — use urls.baseUrl and the correct endpoint key (never hardcode URLs).
   IMPORTANT: The available keys in urls are: baseUrl, login, health_check, profile, notes.
   Construct full URLs like: `${urls.baseUrl}${urls.notes}` or `${urls.baseUrl}${urls.notes}/${id}`.
   NEVER invent new property names like urls.createNote or urls.deleteNote — they do not exist.
3. Read ../../config/scenarios.ts — pick the right executor name to import.
4. Read ../../.env — note current values; update only keys the user explicitly set (sed -i).
5. Read ../../config/options.ts — use customOptions directly. If the user specified custom thresholds or per-operation SLOs, create ../../ai-performance/config/options.ts with the overrides and import from there instead. NEVER inline threshold overrides inside the test file's options object.
6. Build options and write the test script to ../../ai-performance/tests/<name>.ts.
7. Register the test in the build system by updating BOTH files (replace in place — never add new lines):
   a. Update the webpack entry to use the new test name as the key and file path:
        sed -i "s|'.*': '\./ai-performance/tests/.*'|'<name>': './ai-performance/tests/<name>.ts'|" ../../webpack.config.js
   b. Update the "ai:test" script in package.json to reference the new dist file:
        sed -i 's|"ai:test": ".*"|"ai:test": "webpack \&\& dotenv k6 run dist/<name>.js"|' ../../package.json
   Verify both were updated:
        grep '<name>' ../../webpack.config.js
        grep 'ai:test' ../../package.json
8. Verify: ls ../../ai-performance/tests/
9. Print run command: npm run ai:test
   (must be run from the project root, not from ai-playground/)


## Case B — Custom API (api_type: custom)

Use when the test targets any API other than the Notes API.

### Reuse vs. Scaffold Decision

For each support file, decide whether to CREATE a new one in ../../ai-performance/ or REUSE the framework source via ../../ import:

| File | CREATE in ai-performance/ when… | REUSE from framework (../../) when… |
|------|----------------------------------|--------------------------------------|
| data/constants.ts | API has a different base URL or different endpoint paths | — always create; URLs are always API-specific |
| data/<name>-data.ts | Test request provides test_data payloads | No test data needed |
| helpers/setup.ts | API requires different auth (bearer token, basic auth, api-key) | API has no auth, or auth is same as Notes API |
| helpers/metrics.ts | Never — always reuse | Always reuse via ../../helpers/metrics.ts |
| config/scenarios.ts | Never — always reuse | Always reuse via ../../config/scenarios.ts |
| config/options.ts | User specifies different thresholds or per-operation SLOs | Default thresholds are acceptable — reuse via ../../config/options.ts |

**Rule:** Only create a file in ../../ai-performance/ if its content must differ from the framework source. If a file can be used unchanged, import it from ../../ instead.

### Import path rules

Files reused from the framework use ../../ paths:
```typescript
import { requestDuration, requestCount, errorRate, gauge } from '../../helpers/metrics'
import { customOptions }                            from '../../config/options'
import { <scenarioName> }                           from '../../config/scenarios'
```

Files created inside ai-performance/ use ../ paths:
```typescript
import { urls }       from '../data/constants'
import { <dataName> } from '../data/<name>-data'
import { login }      from '../helpers/setup'
import { customOptions } from '../config/options'   // only if a custom options.ts was created
```

### Steps
1. Read ../../tests/e2e.ts to internalise the structural pattern (setup(), default(), group(), check(), metric calls).
2. Read ../../.env — note current values; update only keys the user explicitly set (sed -i).
3. Create ../../ai-performance/data/constants.ts with the base URL and endpoints from the test request.
4. If test_data provided: create ../../ai-performance/data/<name>-data.ts with SharedArray payloads.
5. If API requires auth that differs from the Notes API: create ../../ai-performance/helpers/setup.ts.
   See "HTTP Body Format Rule" below — ALWAYS send request bodies as JSON, never as plain objects.
6. If user specified custom thresholds: create ../../ai-performance/config/options.ts with the overrides; otherwise import customOptions from ../../config/options.ts.
7. Create ../../ai-performance/tests/<name>.ts — import reused files via ../../, local files via ../.
   NEVER inline threshold overrides inside the test file's options object — they always belong in config/options.ts.
8. Register the test in the build system by updating BOTH files (replace in place — never add new lines):
   a. Update the webpack entry to use the new test name as the key and file path:
        sed -i "s|'.*': '\./ai-performance/tests/.*'|'<name>': './ai-performance/tests/<name>.ts'|" ../../webpack.config.js
   b. Update the "ai:test" script in package.json to reference the new dist file:
        sed -i 's|"ai:test": ".*"|"ai:test": "webpack \&\& dotenv k6 run dist/<name>.js"|' ../../package.json
   Verify both were updated:
        grep '<name>' ../../webpack.config.js
        grep 'ai:test' ../../package.json
9. Verify only the folders that were written: ls ../../ai-performance/tests/ (and others as applicable).
10. Print run command: npm run ai:test
    (must be run from the project root, not from ai-playground/)

IMPORTANT for Case B:
- Do NOT create or modify any file in ../../data/, ../../helpers/, ../../config/, or ../../tests/.
- Only create a file in ../../ai-performance/ if its content must differ from the framework source.
- Derive constants.ts content entirely from the base_url and endpoints in the test request.


### HTTP Body Format Rule

k6's `http.post` / `http.put` / `http.patch` send a plain JS object as `application/x-www-form-urlencoded`.
REST APIs expect JSON. ALWAYS use this pattern for any call that sends a request body:

```typescript
http.post(
    url,
    JSON.stringify({ key: value }),
    { headers: { 'Content-Type': 'application/json' } },
)
```

NEVER write: `http.post(url, { key: value })` — this will send form-encoded data and the API will reject it.


## Metric Tag Format
Every API call must record all 4 metrics with this exact tag shape:
```typescript
requestCount.add(1,                        { 'request': 'GET',  'resource': '<resource-name>' })
requestDuration.add(resp.timings.duration, { 'request': 'GET',  'resource': '<resource-name>' })
errorRate.add(resp.status !== 200,         { 'request': 'GET',  'resource': '<resource-name>' })
gauge.add(1,                               { 'request': 'GET',  'resource': '<resource-name>' })
```
Use the HTTP method as 'request' and the resource noun (e.g. 'notes', 'items') as 'resource'.


## Scenario Decision Table
| User intent | Scenario to use | Executor |
|-------------|-----------------|----------|
| "N users for X minutes", "load test", "soak test" | constantVUs | constant-vus |
| "ramp up", "stress test", "find breaking point" | rampingVUs | ramping-vus |
| "X req/sec", "RPS", "arrival rate" | constantArrivalRate | constant-arrival-rate |
| "ramp up RPS", "gradually increase rate" | rampingArrivalRate | ramping-arrival-rate |
| "N total iterations as fast as possible" | sharedIterations | shared-iterations |
| "each VU does N iterations", "partitioned data" | perVUIterations | per-vu-iterations |

If intent is ambiguous, ask ONE clarifying question before generating.


## .env Key Mapping by Scenario
| Scenario | Parameter | .env key |
|----------|-----------|----------|
| constantVUs | VU count | VUS |
| constantVUs | duration | DURATION |
| rampingVUs | initial VU count | START_VUS |
| rampingVUs | stage 1 duration | STAGE_DURATION_1 |
| rampingVUs | stage 1 target VUs | STAGE_TARGET_1 |
| rampingVUs | stage 2 duration | STAGE_DURATION_2 |
| rampingVUs | stage 2 target VUs | STAGE_TARGET_2 |
| rampingVUs | stage 3 duration | STAGE_DURATION_3 |
| rampingVUs | stage 3 target VUs | STAGE_TARGET_3 |
| rampingVUs | graceful ramp down | GRACEFUL_RAMPDOWN |
| sharedIterations | VU count | VUS |
| sharedIterations | total iterations | ITERATIONS |
| sharedIterations | max duration | MAX_DURATION |
| perVUIterations | VU count | VUS |
| perVUIterations | iterations per VU | ITERATIONS |
| perVUIterations | max duration | MAX_DURATION |
| constantArrivalRate | rate (req/time_unit) | RATE |
| constantArrivalRate | duration | DURATION |
| constantArrivalRate | time unit | TIME_UNIT |
| constantArrivalRate | pre-allocated VUs | PRE_ALLOCATED_VUS |
| constantArrivalRate | max VUs | MAX_VUS |
| rampingArrivalRate | starting rate | START_RATE |
| rampingArrivalRate | time unit | TIME_UNIT |
| rampingArrivalRate | stage 1 duration | STAGE_DURATION_1 |
| rampingArrivalRate | stage 1 target rate | STAGE_TARGET_1 |
| rampingArrivalRate | stage 2 duration | STAGE_DURATION_2 |
| rampingArrivalRate | stage 2 target rate | STAGE_TARGET_2 |
| rampingArrivalRate | stage 3 duration | STAGE_DURATION_3 |
| rampingArrivalRate | stage 3 target rate | STAGE_TARGET_3 |
| rampingArrivalRate | pre-allocated VUs | PRE_ALLOCATED_VUS |
| rampingArrivalRate | max VUs | MAX_VUS |


## Threshold Building Rules

### Rule 1 — Only generate thresholds for what the test actually uses
Before writing options.ts, list every threshold you will include by scanning the test you just wrote:
- Which HTTP methods are called? → one Counter + Trend + Rate + Gauge entry per method
- Which named Trend metrics are defined AND have .add() calls? → one per-operation entry each
- Are global thresholds different from the default (500ms / 1%)? → override http_req_duration / http_req_failed

NEVER add a threshold for a method not called in the test.
NEVER add a per-operation threshold for a Trend metric that is not defined and recorded in the test.
NEVER add thresholds "just in case" or as placeholders — every key must have a matching metric at runtime.

### Rule 2 — Structure options.ts with grouped sections and comments

**Case A (framework API):** spread from the framework options.
IMPORTANT: only add threshold keys for methods actually called in the test you generated.

```typescript
import { Options } from 'k6/options';
import { customOptions as frameworkOptions } from '../../config/options';

export const customOptions: Options = {
  ...frameworkOptions,
  thresholds: {
    ...frameworkOptions.thresholds,

    // ── Built-in k6 metrics ──────────────────────────────────────────────────
    'http_req_duration': ['p(95)<Nms'],   // omit if using default 500ms
    'http_req_failed':   ['rate<0.01'],   // omit if using default 1%

    // ── Counter — total requests (one entry per HTTP method used in test) ────
    'request_count{request:GET}':    ['count<N'],
    // 'request_count{request:POST}': ['count<N'],  ← add only if POST used

    // ── Trend — per-method latency SLOs (one entry per HTTP method used) ────
    'request_duration{request:GET}':    ['p(95)<Nms'],

    // ── Rate — per-method error rate (one entry per HTTP method used) ────────
    'error_rate{request:GET}':    ['rate<0.01'],

    // ── Gauge — per-method point-in-time value (one per HTTP method used) ───
    'gauge_count{request:GET}':    ['value>=0'],

    // ── Per-operation Trend SLOs (only if per_operation_thresholds specified) ─
    'create_item_duration': ['p(95)<Nms'],  // only if new Trend(...) + .add() exists in test
  },
};
```

**Case B (custom API):** NEVER spread from the framework options.
The framework's `config/options.ts` contains Notes-API-specific Trend thresholds that do not
exist in any other test — spreading them causes k6 to fail with `no metric name found`.
Write a fully self-contained options.ts with ONLY the thresholds that match the test you generated.

```typescript
import { Options } from 'k6/options';

export const customOptions: Options = {
  thresholds: {

    // ── Built-in k6 metrics ──────────────────────────────────────────────────
    'http_req_duration': ['p(95)<Nms'],
    'http_req_failed':   ['rate<0.01'],

    // ── Counter — total requests (one entry per HTTP method used in test) ────
    'request_count{request:GET}':    ['count<N'],
    // 'request_count{request:POST}': ['count<N'],  ← add only if POST used

    // ── Trend — per-method latency SLOs (one entry per HTTP method used) ────
    'request_duration{request:GET}':    ['p(95)<Nms'],

    // ── Rate — per-method error rate (one entry per HTTP method used) ────────
    'error_rate{request:GET}':    ['rate<0.01'],

    // ── Gauge — per-method point-in-time value (one per HTTP method used) ───
    'gauge_count{request:GET}':    ['value>=0'],

    // ── Per-operation Trend SLOs (only if per_operation_thresholds specified) ─
    'list_cubes_duration': ['p(95)<Nms'],  // only if new Trend(...) + .add() exists in test
  },
};
```

### Rule 3 — Adjust request_count ceiling realistically
- Iteration-based scenarios: `count < (VUs × iterations × requests_per_iteration × 1.1)`
- Duration-based scenarios: raise from default `count<10` to a realistic ceiling
  (e.g. `count<100000` for a short load test, or ask the user if intent is unclear)

### Rule 4 — Named Trend metrics are driven entirely by per_operation_thresholds
ONLY create named Trend metrics when the user explicitly specifies per_operation_thresholds.
NEVER invent Trend metrics on your own — even if they seem useful for per-operation breakdown.

If per_operation_thresholds is specified, all four steps are REQUIRED and must stay in sync.
A Trend defined without a threshold, or a threshold without a Trend, both cause a k6 runtime error:
   a. Import Trend in the test file: `import { Trend } from 'k6/metrics';`
   b. Define at module scope: `const createItemDuration = new Trend('create_item_duration');`
      Naming: operation name + '_duration' (e.g. 'create_item' → 'create_item_duration')
   c. Record inside the group: `createItemDuration.add(resp.timings.duration);`
   d. Add threshold in options.ts under "Per-operation Trend SLOs":
      `'create_item_duration': ['p(95)<500']`  — NO tag filter on named metrics
   - WRONG: `'create_item_duration{request:POST}': ['p(95)<500']`
   - WRONG: defining the Trend metric (steps a–c) without adding the threshold (step d)
   - WRONG: adding the threshold (step d) without defining the Trend (steps a–c)
   - WRONG: inventing Trend metrics not listed in per_operation_thresholds
