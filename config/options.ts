import { perVUIterations, rampingVUs, sharedIterations } from "../config/scenarios.ts";

export const customOptions = {
    thresholds: {
        http_req_duration: ['p(90)<500', 'p(95)<500', 'p(99)<500'],
        http_req_failed: ['rate<0.01'],

        // Counter thresholds — asserts total requests made; catches steps being skipped or over-executed
        'request_count{request:GET}': ['count<10'],
        'request_count{request:POST}': ['count<10'],
        'request_count{request:PUT}': ['count<10'],
        'request_count{request:PATCH}': ['count<10'],
        'request_count{request:DELETE}': ['count<10'],

        // Trend thresholds — asserts latency percentiles (P(90), p95, P(99)); enforces response time SLOs per operation
        'request_duration{request:GET}': ['p(90)<500', 'p(95)<500', 'p(99)<500'],
        'request_duration{request:POST}': ['p(90)<500', 'p(95)<500', 'p(99)<500'],
        'request_duration{request:PUT}': ['p(90)<500', 'p(95)<500', 'p(99)<500'],
        'request_duration{request:PATCH}': ['p(90)<500', 'p(95)<500', 'p(99)<500'],
        'request_duration{request:DELETE}': ['p(90)<500', 'p(95)<500', 'p(99)<500'],

        // Rate thresholds — asserts error rate stays below 1%; fails the test if too many requests return non-200
        'error_rate{request:GET}': ['rate<0.01'],
        'error_rate{request:POST}': ['rate<0.01'],
        'error_rate{request:PUT}': ['rate<0.01'],
        'error_rate{request:PATCH}': ['rate<0.01'],
        'error_rate{request:DELETE}': ['rate<0.01'],

        // Gauge thresholds — asserts the last observed point-in-time value; useful for tracking state like note count or response size
        'gauge_count{request:GET}': ['value>0'],
        'gauge_count{request:POST}': ['value>0'],
        'gauge_count{request:PUT}': ['value>0'],
        'gauge_count{request:PATCH}': ['value>0'],
        'gauge_count{request:DELETE}': ['value>0'],
    },
    scenarios: {
        rampingVUs,
    }
}
