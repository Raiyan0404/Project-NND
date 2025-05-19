from fastapi import FastAPI, Request
import joblib
import pandas as pd
from pydantic import BaseModel
import uvicorn
import psutil
import logging
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load trained model
model_metadata = joblib.load("load_balancer.pkl")
model = model_metadata["model"]
feature_names = model_metadata["features"]
print("Model successfully loaded")

# Define request format
class RequestData(BaseModel):
    cpu: int
    memory: int
    network: int

# Unregister any existing Prometheus collectors to avoid duplication
for coll in list(REGISTRY._collector_to_names.keys()):
    REGISTRY.unregister(coll)

# Define Prometheus metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("http_request_latency_seconds", "HTTP request latency", ["endpoint"])
CPU_USAGE = Gauge("cpu_usage_percent", "CPU usage in percentage")
MEMORY_USAGE = Gauge("memory_usage_percent", "Memory usage in percentage")
REQUEST_SIZE = Histogram("http_request_size_bytes", "Size of HTTP request in bytes", ["endpoint"])
RESPONSE_SIZE = Histogram("http_response_size_bytes", "Size of HTTP response in bytes", ["endpoint"])
ERROR_COUNT = Counter("http_errors_total", "Total number of HTTP errors", ["method", "endpoint", "status_code"])

# Middleware to collect metrics
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

        # Record request size
        request_body = await request.body()
        REQUEST_SIZE.labels(endpoint=endpoint).observe(len(request_body))

        response = await call_next(request)

        # Handle streaming response correctly
        response_size = 0
        if isinstance(response, StreamingResponse):
            response_size = len(await response.body()) if hasattr(response, "body") else 0
        elif hasattr(response, "content"):
            response_size = len(response.content)

        RESPONSE_SIZE.labels(endpoint=endpoint).observe(response_size)

        # Record errors
        if response.status_code >= 400:
            ERROR_COUNT.labels(method=method, endpoint=endpoint, status_code=response.status_code).inc()

        return response

app.add_middleware(MetricsMiddleware)

# Load balancing endpoint
@app.post("/predict")
async def predict(request: Request, data: RequestData):
    logger.info(f"Received request: {data.model_dump()}")  # Log incoming request
    df = pd.DataFrame([data.model_dump()])
    prediction = model.predict(df)[0]
    return {"allocated_server": prediction}

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def get_metrics():
    CPU_USAGE.set(psutil.cpu_percent())
    MEMORY_USAGE.set(psutil.virtual_memory().percent)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Run the API
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
