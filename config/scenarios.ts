// Below two scenarios come under "By number of iterations."
/* This executor is suitable when you want a specific number of VUs to complete a fixed number of total iterations, and the amount of iterations per VU is unimportant. If the time to complete a number of test iterations is your concern, this executor should perform best. */
export const sharedIterations = {
    executor: 'shared-iterations',
    vus: __ENV.VUS,
    iterations: __ENV.ITERATIONS,
    maxDuration: __ENV.MAX_DURATION
}

// Use this executor if you need a specific number of VUs to complete the same number of iterations. This can be useful when you have fixed sets of test data that you want to partition between VUs.
export const perVUIterations = {
    executor: 'per-vu-iterations',
    vus: __ENV.VUS,
    iterations: __ENV.ITERATIONS,
    maxDuration: __ENV.MAX_DURATION
}

// Below two scenarios come under "By number of VUs."
// Use this executor if you need a specific number of VUs to run for a certain amount of time.
export const constantVUs = {
    executor: 'constant-vus',
    vus: __ENV.VUS,
    duration: __ENV.DURATION
}

// This executor is a good fit if you need VUs to ramp up or down during specific periods of time.
export const rampingVUs = {
    executor: 'ramping-vus',
    startVUs: __ENV.START_VUS,
    stages: [
        { duration: '2s', target: 2 },
        { duration: '2s', target: 2 },
        { duration: '2s', target: 0 },
    ],
    gracefulRampDown: __ENV.GRACEFUL_RAMPDOWN,
}

// Below two scenarios come under "By iteration rate."
// When you want iterations to remain constant, independent of the performance of the system under test. This approach is useful for a more accurate representation of RPS
export const constantArrivalRate = {
    executor: 'constant-arrival-rate',
    duration: __ENV.DURATION,
    rate: __ENV.RATE,
    timeUnit: __ENV.TIME_UNIT,
    preAllocatedVUs: __ENV.PRE_ALLOCATED_VUS
}

// If you need start iterations independent of system-under-test performance, and want to ramp the number of iterations up or down during specific periods of time.
export const rampingArrivalRate = {
    executor: 'ramping-arrival-rate',
    startRate: __ENV.START_RATE,
    timeUnit: __ENV.TIME_UNIT,
    stages: [
        { duration: '2s', target: 2 },
        { duration: '2s', target: 4 },
        { duration: '2s', target: 0 },
    ],
    preAllocatedVUs: __ENV.PRE_ALLOCATED_VUS,
    maxVUs: __ENV.MAX_VUS
}
