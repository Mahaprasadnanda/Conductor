import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 10,
    duration: '10s',
};

export default function () {
    // Requires a service and instances to be set up first
    // This script assumes the service is named 'demo'
    const res = http.get('http://localhost:8000/api/v1/gateway/demo/hello', {
        headers: {
            'Authorization': 'Bearer ' + __ENV.TOKEN // Pass token via environment variable
        }
    });

    check(res, {
        'status is 200': (r) => r.status === 200,
        'has instance header': (r) => r.headers['X-Service-Instance'] !== undefined,
        'has strategy header': (r) => r.headers['X-Loadbalancer-Strategy'] !== undefined,
    });
    
    sleep(0.1);
}
