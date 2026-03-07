import http, { head, patch } from 'k6/http';
import { SharedArray } from 'k6/data';
import { check, group } from 'k6';
import { healthCheckCall, login } from '../helpers/setup.ts';
import { urls } from '../data/constants.ts';
import { notes } from '../data/notes-data.ts'
import { customOptions } from '../config/options.ts';
import { requestDuration, requestCount, errorRate, gauge } from '../helpers/metrics.ts';

const sharedData = new SharedArray('notesData', function () {
    return notes;
});

export const options = customOptions;

export function setup() {
    const health = healthCheckCall();
    check(health, {
        'service health should be 200': (resp) => resp === 200,
    });

    const token = login();
    console.log(token);
    return { token };
}

export default async function (data: { token: any; }) {
    const params = { headers: { 'x-auth-token': data.token, 'Content-Type': 'application/json' } };


    // ================= Get notes list ======================
    const getResp = http.get(`${urls.baseUrl}${urls.notes}`, params);
    const getBody = JSON.parse(getResp.body as string);

    check(getResp, {
        'get status is 200': (resp) => resp.status === 200,
        'get success is true': () => getBody.success === true,
        'data empty []': () => getBody.data.length === 0,
    });
    requestCount.add(1, { 'request': 'GET', 'resource': 'notes' });
    requestDuration.add(getResp.timings.duration, { 'request': 'GET', 'resource': 'notes' });
    errorRate.add(getResp.status !== 200, { 'request': 'GET', 'resource': 'notes' });
    gauge.add(1, { 'request': 'GET', 'resource': 'notes' })
    console.log(`Get Response: ${JSON.stringify(getBody)}`);


    // ================== Create notes =======================
    const sharedDataIndex = Math.floor(Math.random() * sharedData.length);
    const pickedArray = sharedData[sharedDataIndex];

    // Create API call
    const createResp = http.post(`${urls.baseUrl}${urls.notes}`, JSON.stringify(pickedArray), params);
    const createBody = await JSON.parse(createResp.body as string);
    const noteId: string = await createBody.data.id;

    check(createResp, {
        'create status is 200': (resp) => resp.status === 200,
        'create success is true': () => createBody.success === true,
        'notes title is present': () => createBody.data.title === pickedArray.title,
        'notes description is present': () => createBody.data.description === pickedArray.description,
        'notes category is present': () => createBody.data.category === pickedArray.category,
        'notes completed should be false': () => createBody.data.completed === false,
    });
    requestCount.add(1, { 'request': 'POST', 'resource': 'notes' });
    requestDuration.add(createResp.timings.duration, { 'request': 'POST', 'resource': 'notes' });
    errorRate.add(createResp.status !== 200, { 'request': 'POST', 'resource': 'notes' });
    gauge.add(1, { 'request': 'POST', 'resource': 'notes' })
    console.log(`Create Response: ${JSON.stringify(createBody)}`);


    // ================= Edit notes call ======================
    const editSharedDataIndex = (sharedDataIndex + 1) % sharedData.length;
    const editPayload = {
        id: noteId,
        title: pickedArray.title + ' - Edited',
        description: pickedArray.description + ' - Edited',
        category: sharedData[editSharedDataIndex].category,
        completed: true,
    };

    // Edit API call
    const editResp = http.put(`${urls.baseUrl}${urls.notes}/${noteId}`, JSON.stringify(editPayload), params);
    const editBody = JSON.parse(editResp.body as string);

    check(editResp, {
        'edit status is 200': (editResp) => editResp.status === 200,
        'edit success is true': () => editBody.success === true,
        'edit id should match': () => editBody.data.id === noteId,
        'edit title should match': () => editBody.data.title === editPayload.title,
        'edit description should match': () => editBody.data.description === editPayload.description,
        'edit category should match': () => editBody.data.category === editPayload.category,
        'edit completed should match': () => editBody.data.completed === editPayload.completed,
    });
    requestCount.add(1, { 'request': 'PUT', 'resource': 'notes' });
    requestDuration.add(editResp.timings.duration, { 'request': 'PUT', 'resource': 'notes' });
    errorRate.add(editResp.status !== 200, { 'request': 'PUT', 'resource': 'notes' });
    gauge.add(1, { 'request': 'PUT', 'resource': 'notes' })
    console.log(`Edit Response: ${JSON.stringify(editBody)}`);


    // ================= Patch notes call ======================
    const patchPayload = { id: noteId, completed: false };

    const patchResp = http.patch(`${urls.baseUrl}${urls.notes}/${noteId}`, JSON.stringify(patchPayload), params);
    const patchBody = JSON.parse(patchResp.body as string);

    check(patchResp, {
        'patch status is 200': (editResp) => editResp.status === 200,
        'patch success is true': () => patchBody.success === true,
        'patch id should match': () => patchBody.data.id === noteId,
        'patch title should match': () => patchBody.data.title === editPayload.title,
        'patch description should match': () => patchBody.data.description === editPayload.description,
        'patch category should match': () => patchBody.data.category === editPayload.category,
        'patch completed should match': () => patchBody.data.completed === false,
    });
    requestCount.add(1, { 'request': 'PATCH', 'resource': 'notes' });
    requestDuration.add(patchResp.timings.duration, { 'request': 'PATCH', 'resource': 'notes' });
    errorRate.add(patchResp.status !== 200, { 'request': 'PATCH', 'resource': 'notes' });
    gauge.add(1, { 'request': 'PATCH', 'resource': 'notes' })
    console.log(`Patch Response: ${JSON.stringify(patchResp)}`);


    // ================= Delete notes call ======================
    const delResponse = http.del(`${urls.baseUrl}${urls.notes}/${noteId}`, JSON.stringify({}), params);
    const delBody = JSON.parse(delResponse.body as string);

    check(delResponse, {
        'del status is 200': (resp) => resp.status === 200,
        'del success is true': () => delBody.success === true,
        'del message pass': () => delBody.message === 'Note successfully deleted',
    });
    requestCount.add(1, { 'request': 'DELETE', 'resource': 'notes' });
    requestDuration.add(delResponse.timings.duration, { 'request': 'DELETE', 'resource': 'notes' });
    errorRate.add(delResponse.status !== 200, { 'request': 'DELETE', 'resource': 'notes' });
    gauge.add(1, { 'request': 'DELETE', 'resource': 'notes' })
    console.log(`Delete Response: ${JSON.stringify(delBody)}`);
}
