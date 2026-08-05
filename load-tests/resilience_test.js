import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 10,
    duration: '15s',
};

export default function () {
    // Requires a service setup that periodically fails or is completely down
    // Testing fallback behavior
    const url = 'http://host.docker.internal:8000/api/v1/gateway/resilient_service/test';

    const res = http.get(url);

    check(res, {
        'status is 200 or 503': (r) => r.status === 200 || r.status === 503,
        'has fallback header': (r) => r.headers['X-Circuit-State'] !== undefined,
    });

    sleep(0.1);
}
