import time
import random
from flask import Flask, Response, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Metrics
# Using a fixed set of buckets to avoid unbounded growth and ensure suitability for the /slow endpoint
REQUESTS = Counter(
    'slo_demo_http_requests_total',
    'Total HTTP requests',
    ['method', 'route', 'status']
)

LATENCY = Histogram(
    'slo_demo_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'route'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

@app.before_request
def start_timer():
    request.start_time = time.perf_counter()

@app.after_request
def record_metrics(response):
    # Normalize route names
    if request.url_rule:
        route = request.url_rule.rule
    else:
        route = 'unknown'

    # Do not record /metrics and /healthz as service-level traffic
    if route in ['/metrics', '/healthz']:
        return response
    
    latency = time.perf_counter() - request.start_time
    
    REQUESTS.labels(
        method=request.method,
        route=route,
        status=str(response.status_code)
    ).inc()
    
    LATENCY.labels(
        method=request.method,
        route=route
    ).observe(latency)
    
    return response

@app.route('/')
def root():
    return "OK", 200

@app.route('/fail')
def fail():
    return "Internal Server Error", 500

@app.route('/slow')
def slow():
    # Simulate a slow response between 0.5 and 2.0 seconds
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)
    return f"Response delayed by {delay:.2f}s", 200

@app.route('/healthz')
def healthz():
    return "OK", 200

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    # Flask development server is sufficient for this demo
    app.run(host='0.0.0.0', port=8080)
