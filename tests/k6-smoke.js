import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/healthz`);
  check(healthRes, {
    'healthz returns 200': (r) => r.status === 200,
  });

  // API root redirect
  const rootRes = http.get(`${BASE_URL}/`, { redirects: 0 });
  check(rootRes, {
    'root returns redirect or 200': (r) => r.status === 200 || r.status === 307,
  });

  // Search endpoint (if available)
  const searchRes = http.get(`${BASE_URL}/api/search?q=adhesive`);
  check(searchRes, {
    'search returns 200': (r) => r.status === 200,
    'search response time < 1s': (r) => r.timings.duration < 1000,
  });

  sleep(1);
}
