import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
    vus: 50, // 50 Virtual Users
    duration: '10s', // For 10 seconds
};

export default function () {
    let res = http.get('http://host.docker.internal:8000/api/v1/gateway/test-service/path');
    
    // We expect 200 OK initially, and 429 Too Many Requests once limit is reached
    check(res, {
        'status is 200 or 429': (r) => r.status === 200 || r.status === 429,
        'rate limit remaining is present': (r) => r.headers['X-Ratelimit-Remaining'] !== undefined,
    });
    
    sleep(0.1);
}
