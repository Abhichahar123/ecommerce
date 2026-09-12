from locust import HttpUser, task, between
import random


class EcommerceUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.post(
            "http://127.0.0.1:8001/auth/login",
            json={
                "email": "test@example.com",
                "password": "mypassword123"
            }
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def get_products(self):
        self.client.get("http://127.0.0.1:8002/products/")

    @task(3)
    def get_single_product(self):
        product_id = random.randint(1, 2)
        self.client.get(f"http://127.0.0.1:8002/products/{product_id}")

    @task(2)
    def get_my_orders(self):
        if self.token:
            try:
                response = self.client.get(
                    "http://127.0.0.1:8003/orders/",
                    headers=self.headers,
                    name="/orders/"
                )
                # Token expire ho gaya → dobara login karo
                if response.status_code == 401:
                    self.on_start()
            except:
                pass

    @task(1)
    def check_auth(self):
        self.client.get("http://127.0.0.1:8001/health")