import { Counter, Trend, Rate, Gauge } from "k6/metrics";

export const requestDuration = new Trend('request_duration');
export const requestCount = new Counter('request_count');
export const errorRate = new Rate('error_rate');
export const gauge = new Gauge('gauge_count');
