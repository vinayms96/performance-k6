// Below two scenarios come under "By number of iterations."
/* This executor is suitable when you want a specific number of VUs to complete a fixed number of total iterations, and the amount of iterations per VU is unimportant. If the time to complete a number of test iterations is your concern, this executor should perform best. */
export const sharedIterations = {
    executor: 'shared-iterations',
    vus: parseInt(__ENV.VUS),
    iterations: parseInt(__ENV.ITERATIONS),
    maxDuration: __ENV.MAX_DURATION
}

// Use this executor if you need a specific number of VUs to complete the same number of iterations. This can be useful when you have fixed sets of test data that you want to partition between VUs.
export const perVUIterations = {
    executor: 'per-vu-iterations',
    vus: parseInt(__ENV.VUS),
    iterations: parseInt(__ENV.ITERATIONS),
    maxDuration: __ENV.MAX_DURATION
}

// Below two scenarios come under "By number of VUs."
// Use this executor if you need a specific number of VUs to run for a certain amount of time.
export const constantVUs = {
    executor: 'constant-vus',
    vus: parseInt(__ENV.VUS),
    duration: __ENV.DURATION
}

// This executor is a good fit if you need VUs to ramp up or down during specific periods of time.
export const rampingVUs = {
    executor: 'ramping-vus',
    startVUs: parseInt(__ENV.START_VUS),
    stages: [
        { duration: __ENV.STAGE_DURATION_1, target: parseInt(__ENV.STAGE_TARGET_1) },
        { duration: __ENV.STAGE_DURATION_2, target: parseInt(__ENV.STAGE_TARGET_2) },
        { duration: __ENV.STAGE_DURATION_3, target: parseInt(__ENV.STAGE_TARGET_3) },
    ],
    gracefulRampDown: __ENV.GRACEFUL_RAMPDOWN,
}

// Below two scenarios come under "By iteration rate."
// When you want iterations to remain constant, independent of the performance of the system under test. This approach is useful for a more accurate representation of RPS
export const constantArrivalRate = {
    executor: 'constant-arrival-rate',
    duration: __ENV.DURATION,
    rate: parseInt(__ENV.RATE),
    timeUnit: __ENV.TIME_UNIT,
    preAllocatedVUs: parseInt(__ENV.PRE_ALLOCATED_VUS),
    maxVUs: parseInt(__ENV.MAX_VUS)
}

// If you need start iterations independent of system-under-test performance, and want to ramp the number of iterations up or down during specific periods of time.
export const rampingArrivalRate = {
    executor: 'ramping-arrival-rate',
    startRate: parseInt(__ENV.START_RATE),
    timeUnit: __ENV.TIME_UNIT,
    stages: [
        { duration: __ENV.STAGE_DURATION_1, target: parseInt(__ENV.STAGE_TARGET_1) },
        { duration: __ENV.STAGE_DURATION_2, target: parseInt(__ENV.STAGE_TARGET_2) },
        { duration: __ENV.STAGE_DURATION_3, target: parseInt(__ENV.STAGE_TARGET_3) },
    ],
    preAllocatedVUs: parseInt(__ENV.PRE_ALLOCATED_VUS),
    maxVUs: parseInt(__ENV.MAX_VUS)
}
