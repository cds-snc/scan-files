from locust import HttpUser, task
import os
import tempfile


def random_file():
    fout = tempfile.TemporaryFile()
    fout.write(os.urandom(1024))
    fout.seek(0)
    return open(fout, "rb")


class APIUser(HttpUser):
    @task
    def run_flow(self):
        attach = random_file()
        response = self.client.post("/assemblyline", files={"file": attach})
        results = response.json()
        self.client.get(f"/assemblyline/{results['scan_id']}")
