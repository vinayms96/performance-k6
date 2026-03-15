# Performance Test Request
# 1. Fill in the USER FORM below.
# 2. Generate: python3 generate.py             (defaults to --ai claude)
#              python3 generate.py --ai openai  (or --ai claude)
# 3. Run the printed npm command from the PROJECT ROOT (not from ai-playground/)
#    e.g.  npm run test:<name>

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          USER FORM — EDIT THIS                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

## 1. API Type
# "framework" → Notes API (reuses all framework files, only generates test script)
# "custom"    → Any other API (see AI Reference below for what gets generated)
api_type: custom


## 2. API Details  (skip if api_type is "framework")

base_url: https://api.datausa.io/tesseract
authentication: none          # none | bearer-token | basic-auth | api-key

# auth_details: |
#   POST /auth/login
#   Body: { "username": __ENV.EMAIL, "password": __ENV.PASSWORD }
#   Extract token from: body.data.token
#   Attach as header: Authorization: Bearer <token>

# endpoints:
  - method: GET
    path: /cubes
    description: List all cubes that is present in body.cubes[]
  - method: GET
    path: /cubes/<cubesId>
    description: List specific cube data
#   - method: POST
#     path: /items
#     description: Create item
#     body: |
#       { "name": "Item {{ __ITER }}", "quantity": 1 }
#   - method: DELETE
#     path: /items/:id
#     description: Delete item (id from POST response body.data.id)

# test_data: |
#   [
#     { "name": "Load Test Item 1", "quantity": 10 },
#     { "name": "Load Test Item 2", "quantity": 20 }
#   ]


## 3. Scenario
# constantVUs | rampingVUs | sharedIterations | perVUIterations | constantArrivalRate | rampingArrivalRate
scenario: rampingArrivalRate


## 4. Load Parameters  (uncomment and set only what your scenario uses)

vus: 3            # constantVUs / sharedIterations / perVUIterations
duration: 5s     # constantVUs / constantArrivalRate

# iterations: 10    # sharedIterations (total) / perVUIterations (per VU)
# max_duration: 60s # sharedIterations / perVUIterations

# start_vus: 0           # rampingVUs
# graceful_rampdown: 2s # rampingVUs
stage_duration_1: 2s  # rampingVUs / rampingArrivalRate
stage_target_1: 3      # rampingVUs (VUs) / rampingArrivalRate (RPS)
stage_duration_2: 2s
stage_target_2: 3
stage_duration_3: 2s
stage_target_3: 0

# rate: 5                # constantArrivalRate
start_rate: 0            # rampingArrivalRate
time_unit: 1s            # constantArrivalRate / rampingArrivalRate
pre_allocated_vus: 3     # constantArrivalRate / rampingArrivalRate
max_vus: 5               # constantArrivalRate / rampingArrivalRate


## 5. Performance Targets  (defaults: p95 < 500ms, error rate < 1% — leave blank to keep defaults)

global_p95_ms: 400
global_error_rate_pct: 1

# per_operation_thresholds: add ONLY for operations that need individual SLOs beyond the global target.
# Each 'operation' value becomes a Trend metric named '<operation>_duration' in the test file.
# The AI will: (a) import Trend, (b) define the metric, (c) record it in the group, (d) add the threshold.
# per_operation_thresholds:
#   - operation: <name>
#       p95_ms: 400


## 6. Test Flow
flow: |
  1. GET /cubes — list all cubes
  2. Extract the first cube id from body.cubes[0].id
  3. GET /cubes/<cubeId> — fetch that cube's detail


## 7. Additional Notes  (optional — any extra instructions for the AI)
notes: |
  Wrap each operation in a group() block.
  Only GET requests — no auth, no test data, no setup().


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║              AI REFERENCE — DO NOT EDIT (read by AI, not user)               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# --- api_type behaviour ---
#
#   framework → Generate ONLY ai-performance/tests/<name>.ts
#               Import everything from framework via ../../ paths
#
#   custom    → Always create:
#                 ai-performance/data/constants.ts   (base URL + endpoints)
#                 ai-performance/tests/<name>.ts
#               Create only if content differs from framework:
#                 ai-performance/data/<name>-data.ts  (only if test_data provided)
#                 ai-performance/helpers/setup.ts     (only if auth differs from Notes API)
#                 ai-performance/config/options.ts    (only if custom thresholds specified)
#               Always reuse from framework via ../../ (never copy):
#                 helpers/metrics.ts, config/scenarios.ts

# --- scenario → when to use ---
#
#   constantVUs         — fixed VUs for a set duration           (load / soak test)
#   rampingVUs          — VUs ramp up/down across 3 stages       (stress / spike test)
#   sharedIterations    — fixed total iterations across VUs      (smoke / finite run)
#   perVUIterations     — each VU runs N iterations              (partitioned data)
#   constantArrivalRate — fixed RPS regardless of response time  (throughput test)
#   rampingArrivalRate  — RPS ramps up/down across 3 stages      (capacity ramp test)

# --- threshold types → when to use ---
#
#   Counter  (count<N)           — verify total requests made; catches skipped/over-executed steps
#                                  AVOID with rampingVUs — high VU count will breach fixed limits
#   Trend    (p(90/95/99)<Nms)  — enforce latency SLOs per operation; always use in load tests
#   Rate     (rate<0.01)         — fail if error frequency exceeds threshold; pair with Trend
#   Gauge    (value>N/value<N)   — assert last observed point-in-time value (count, size, etc.)

# --- .env key mapping (for AI to update via sed -i) ---
#
#   vus               → VUS              (constantVUs / sharedIterations / perVUIterations)
#   duration          → DURATION         (constantVUs / constantArrivalRate)
#   iterations        → ITERATIONS       (sharedIterations / perVUIterations)
#   max_duration      → MAX_DURATION     (sharedIterations / perVUIterations)
#   start_vus         → START_VUS        (rampingVUs)
#   graceful_rampdown → GRACEFUL_RAMPDOWN (rampingVUs)
#   stage_duration_1  → STAGE_DURATION_1 (rampingVUs / rampingArrivalRate)
#   stage_target_1    → STAGE_TARGET_1   (rampingVUs / rampingArrivalRate)
#   stage_duration_2  → STAGE_DURATION_2
#   stage_target_2    → STAGE_TARGET_2
#   stage_duration_3  → STAGE_DURATION_3
#   stage_target_3    → STAGE_TARGET_3
#   rate              → RATE             (constantArrivalRate / rampingArrivalRate)
#   start_rate        → START_RATE       (rampingArrivalRate)
#   time_unit         → TIME_UNIT        (constantArrivalRate / rampingArrivalRate)
#   pre_allocated_vus → PRE_ALLOCATED_VUS
#   max_vus           → MAX_VUS
