from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os
import psutil
import threading
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
CORS(app)

# Metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
LATENCY = Gauge("http_request_latency_seconds", "HTTP request latency")
CPU_USAGE = Gauge("cpu_usage_percent", "CPU usage in percentage")
MEMORY_USAGE = Gauge("memory_usage_percent", "Memory usage in percentage")
REQUEST_SIZE = Gauge("http_request_size_bytes", "Size of HTTP request in bytes")
RESPONSE_SIZE = Gauge("http_response_size_bytes", "Size of HTTP response in bytes")

# Track requests per allocated server
MODEL_REQUEST_COUNT = Counter("model_requests_total", "Total requests per allocated server", ["server"])

SERVER_ALLOCATIONS = {"AWS": 0, "GCP": 0, "Azure": 0}

def allocate_server(cpu, memory, network):
    if cpu > 80 or memory > 80 or network > 80:
        return "Azure"
    elif cpu > 50 or memory > 50 or network > 50:
        return "GCP"
    else:
        return "AWS"

@app.route("/predict", methods=["POST"])
def handle_workload():
    global SERVER_ALLOCATIONS
    start_time = time.time()
    
    data = request.get_json()
    
    # Record request size
    REQUEST_SIZE.set(len(str(data)))
    
    allocated_server = allocate_server(data["cpu"], data["memory"], data["network"])
    
    # Update metrics
    REQUEST_COUNT.labels(method="POST", endpoint="/predict").inc()
    MODEL_REQUEST_COUNT.labels(server=allocated_server).inc()
    SERVER_ALLOCATIONS[allocated_server] += 1

    # Simulate some CPU work
    _ = [i * i for i in range(10000)]  # Small computational task

    latency = time.time() - start_time
    LATENCY.set(latency)
    
    response = jsonify({
        "allocated_server": allocated_server,
        "balancer_type": "traditional",
        "latency": latency
    })
    
    # Record response size
    RESPONSE_SIZE.set(len(response.data))

    return response

@app.route("/metrics")
def metrics():
    MEMORY_USAGE.set(psutil.virtual_memory().percent)
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

# Background thread to monitor CPU usage
def update_cpu_usage():
    while True:
        CPU_USAGE.set(psutil.cpu_percent(interval=1))
        time.sleep(1)  # Update every second

cpu_thread = threading.Thread(target=update_cpu_usage, daemon=True)
cpu_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, threaded=True)
