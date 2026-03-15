import { rampingVUs, sharedIterations, rampingArrivalRate } from "../config/scenarios";

export const customOptions = {
import { rampingArrivalRate } from "../config/scenarios";
    thresholds: {
        create_item_duration: ['p(95)<400'],
        edit_item_duration: ['p(95)<400'],
        delete_item_duration: ['p(95)<400'],
        http_req_duration: ['p(90)<400', 'p(95)<400', 'p(99)<400'],
        http_req_failed: ['rate<0.01'],

        // Counter (count<N) — use to verify total requests made across the run; catches skipped/over-executed steps or caps volume.
        // Avoid with rampingVUs at high concurrency — VU count inflates totals and will breach fixed limits.
        'request_count{request:GET}': ['count<10'],
        'request_count{request:POST}': ['count<10'],
        'request_count{request:PUT}': ['count<10'],
        'request_count{request:PATCH}': ['count<10'],
        'request_count{request:DELETE}': ['count<10'],

        // Trend (p(90/95/99)<Nms) — use to enforce latency SLOs per operation; always include in load/stress/soak tests.
        'request_duration{request:GET}': ['p(90)<400', 'p(95)<400', 'p(99)<400'],
        'request_duration{request:POST}': ['p(90)<400', 'p(95)<400', 'p(99)<400'],
        'request_duration{request:PUT}': ['p(90)<400', 'p(95)<400', 'p(99)<400'],
        'request_duration{request:PATCH}': ['p(90)<400', 'p(95)<400', 'p(99)<400'],
        'request_duration{request:DELETE}': ['p(90)<400', 'p(95)<400', 'p(99)<400'],

        // Rate (rate<0.01) — use to fail the test if error frequency exceeds a threshold; always pair with Trend thresholds.
        'error_rate{request:GET}': ['rate<0.01'],
        'error_rate{request:POST}': ['rate<0.01'],
        'error_rate{request:PUT}': ['rate<0.01'],
        'error_rate{request:PATCH}': ['rate<0.01'],
        'error_rate{request:DELETE}': ['rate<0.01'],

        // Gauge (value>N / value<N) — use for end-state point-in-time checks (e.g. note count, response size); not an aggregate.
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
