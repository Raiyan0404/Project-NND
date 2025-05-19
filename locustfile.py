from locust import HttpUser, task, between

class LoadTestFastAPI(HttpUser):
    wait_time = between(1, 3)
    host = "http://127.0.0.1:8000"  # FastAPI ML-Optimized Load Balancer

    @task
    def test_ml_load_balancer(self):
        test_data = [
            {"cpu": 10, "memory": 20, "network": 15},
            {"cpu": 50, "memory": 60, "network": 70}
        ]
        for data in test_data:
            self.client.post("/predict", json=data)

class LoadTestFlask(HttpUser):
    wait_time = between(1, 3)
    host = "http://127.0.0.1:8002"  # Flask Traditional Load Balancer

    @task
    def test_traditional_load_balancer(self):
        test_data = [
            {"cpu": 10, "memory": 20, "network": 15},
            {"cpu": 50, "memory": 60, "network": 70}
        ]
        for data in test_data:
            self.client.post("/predict", json=data)
