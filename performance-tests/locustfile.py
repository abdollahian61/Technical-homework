from locust import HttpUser, task, between, events
import random
import string
import time

class FastAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        self.client.verify = False
        self.test_keys = []
    
    @task(3)
    def write_to_redis(self):
        """Write data to Redis - weighted 3x"""
        key = f"load_test_{''.join(random.choices(string.ascii_lowercase, k=10))}"
        value = f"value_{''.join(random.choices(string.ascii_letters + string.digits, k=20))}"
        
        with self.client.post(
            f"/write/{key}",
            params={"value": value},
            catch_response=True,
            name="/write/[key]"
        ) as response:
            if response.status_code == 200:
                response.success()
                self.test_keys.append(key)
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(5)
    def read_from_redis(self):
        """Read data from Redis - weighted 5x"""
        with self.client.get(
            "/",
            catch_response=True,
            name="/"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Health check endpoint - weighted 1x"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                if response.json().get("status") == "healthy":
                    response.success()
                else:
                    response.failure("Service unhealthy")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """Metrics endpoint - weighted 1x"""
        with self.client.get(
            "/metrics",
            catch_response=True,
            name="/metrics"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Performance test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Performance test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")
