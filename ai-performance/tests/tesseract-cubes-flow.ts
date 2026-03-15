import http from 'k6/http';
import { check, group } from 'k6';
import { urls } from '../data/constants';
import { customOptions } from '../config/options';
import { requestDuration, requestCount, errorRate, gauge } from '../../helpers/metrics';

export const options = customOptions;

export default function () {
    let cubeId: string = '';

    // ── Group 1: List all cubes ──────────────────────────────────────────────
    group('list cubes', function () {
        const resp = http.get(`${urls.baseUrl}${urls.cubes}`);
        const body = JSON.parse(resp.body as string);

        check(resp, {
            'list cubes status is 200': (r) => r.status === 200,
            'list cubes body has cubes array': () => Array.isArray(body.cubes),
            'list cubes array is not empty': () => body.cubes.length > 0,
        });

        requestCount.add(1,                        { 'request': 'GET', 'resource': 'cubes' });
        requestDuration.add(resp.timings.duration, { 'request': 'GET', 'resource': 'cubes' });
        errorRate.add(resp.status !== 200,         { 'request': 'GET', 'resource': 'cubes' });
        gauge.add(1,                               { 'request': 'GET', 'resource': 'cubes' });

        if (body.cubes && body.cubes.length > 0) {
            cubeId = body.cubes[0].name;
        }

        console.log(`List Cubes — status: ${resp.status}, cubeId: ${cubeId}`);
    });

    // ── Group 2: Fetch specific cube detail ──────────────────────────────────
    group('get cube detail', function () {
        if (!cubeId) {
            console.warn('No cubeId extracted — skipping get cube detail');
            return;
        }

        const resp = http.get(`${urls.baseUrl}${urls.cubes}/${cubeId}`);
        const body = JSON.parse(resp.body as string);

        check(resp, {
            'get cube detail status is 200': (r) => r.status === 200,
            'get cube detail has name': () => body.name !== undefined || (body.cubes && body.cubes.length > 0),
        });

        requestCount.add(1,                        { 'request': 'GET', 'resource': 'cubes' });
        requestDuration.add(resp.timings.duration, { 'request': 'GET', 'resource': 'cubes' });
        errorRate.add(resp.status !== 200,         { 'request': 'GET', 'resource': 'cubes' });
        gauge.add(1,                               { 'request': 'GET', 'resource': 'cubes' });

        console.log(`Get Cube Detail — cubeId: ${cubeId}, status: ${resp.status}`);
    });
}
