from locust import HttpUser, task
import os
import tempfile


# Generate random file
def random_file():
    fout = tempfile.NamedTemporaryFile()
    fout.write(os.urandom(1024))
    fout.seek(0)
    return open(fout.name, "rb")


class APIUser(HttpUser):
    @task
    def run_flow(self):
        attach = random_file()
        response = self.client.post("/assemblyline", files={"file": attach})
        results = response.json()
        self.client.get(f"/assemblyline/{results['scan_id']}")

    def on_start(self):
        self.client.headers.update({"Authorization": os.environ.get("API_AUTH_TOKEN")})
