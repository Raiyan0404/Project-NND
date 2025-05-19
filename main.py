from flask import Flask, request, jsonify
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus metric: Total workload requests received
workload_requests = Counter('workload_requests_total', 'Total workload requests received')

# Prometheus metric: Server allocations labeled by server type
server_allocations = Counter('server_allocations_total', 'Total number of server allocations', ['server'])

# Server allocation logic (Simple Rule-Based)
def allocate_server(cpu, memory, network):
    if cpu > 80 or memory > 80 or network > 80:
        return "Azure"  # Heavy workload
    else:
        return "AWS"  # Light workload

# Endpoint to handle workload allocation
@app.route('/allocate_workload', methods=['POST'])
def handle_workload():
    data = request.get_json()
    cpu = data.get('cpu')
    memory = data.get('memory')
    network = data.get('network')

    if cpu is None or memory is None or network is None:
        return jsonify({'error': 'Invalid workload data'}), 400

    # Increment Prometheus counter for workload requests
    workload_requests.inc()

    # Allocate server based on logic
    allocated_server = allocate_server(cpu, memory, network)

    # Increment allocation counter for that server (AWS or Azure)
    server_allocations.labels(server=allocated_server).inc()

    return jsonify({'allocated_server': allocated_server})

# Endpoint for Prometheus metrics
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
