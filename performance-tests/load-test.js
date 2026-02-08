import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const requestDuration = new Trend('request_duration');
const requestCount = new Counter('request_count');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],                  // Error rate < 1%
    errors: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Test 1: Health check
  let healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 200ms': (r) => r.timings.duration < 200,
  });

  // Test 2: Write to Redis
  const writeKey = `test_key_${__VU}_${__ITER}`;
  const writeValue = `test_value_${Date.now()}`;
  
  let writeRes = http.post(`${BASE_URL}/write/${writeKey}?value=${writeValue}`);
  let writeSuccess = check(writeRes, {
    'write status is 200': (r) => r.status === 200,
    'write response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!writeSuccess);
  requestDuration.add(writeRes.timings.duration);
  requestCount.add(1);

  sleep(0.5);

  // Test 3: Read from Redis
  let readRes = http.get(`${BASE_URL}/`);
  let readSuccess = check(readRes, {
    'read status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'read response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!readSuccess);
  requestDuration.add(readRes.timings.duration);
  requestCount.add(1);

  sleep(1);

  // Test 4: Metrics endpoint
  let metricsRes = http.get(`${BASE_URL}/metrics`);
  check(metricsRes, {
    'metrics status is 200': (r) => r.status === 200,
    'metrics response time < 300ms': (r) => r.timings.duration < 300,
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    'performance-results/summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  // Custom text summary for console output
  return `
  ========================================
  Performance Test Summary
  ========================================
  Total Requests: ${data.metrics.http_reqs.values.count}
  Failed Requests: ${data.metrics.http_req_failed.values.passes}
  Request Duration (avg): ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
  Request Duration (p95): ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
  Request Duration (p99): ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms
  Error Rate: ${(data.metrics.errors?.values.rate * 100 || 0).toFixed(2)}%
  ========================================
  `;
}
