import { Options } from 'k6/options';
import { rampingArrivalRate } from '../../config/scenarios';

export const customOptions: Options = {
    thresholds: {

        // ── Built-in k6 metrics ──────────────────────────────────────────────────
        'http_req_duration': ['p(95)<400'],
        'http_req_failed':   ['rate<0.01'],

        // ── Counter — total requests (GET only) ──────────────────────────────────
        'request_count{request:GET}': ['count<200'],

        // ── Trend — per-method latency SLOs ─────────────────────────────────────
        'request_duration{request:GET}': ['p(95)<400'],

        // ── Rate — per-method error rate ─────────────────────────────────────────
        'error_rate{request:GET}': ['rate<0.01'],

        // ── Gauge — per-method point-in-time value ───────────────────────────────
        'gauge_count{request:GET}': ['value>=0'],
    },
    scenarios: {
        rampingArrivalRate,
    },
};
