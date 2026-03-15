import http from 'k6/http';
import { urls } from '../data/constants';
import { users } from '../data/users';

/**
 * Logs into the user account
 * @returns the login token
 */
export function login(): string {
    const randomAccounts = Math.floor(Math.random() * users.length);
    const response = http.post(`${urls.baseUrl}${urls.login}`, {
        email: users[randomAccounts],
        password: __ENV.PASSWORD,
    });

    return JSON.parse(response.body as string).data.token;
}

export function healthCheckCall(): number {
    const response = http.get(`${urls.baseUrl}${urls.health_check}`);
    return response.status;
}
