"""
Performance testing for the scanning endpoints.  Creates
a ramdom file and uploads it to the endpoint to trigger
a scan.
"""
from locust import HttpUser, task
import os
import tempfile

AV_ENDPOINT = os.environ.get("AV_ENDPOINT", "/clamav")


def random_file():
    "Generate random file"
    fout = tempfile.NamedTemporaryFile()
    fout.write(os.urandom(1024))
    fout.seek(0)
    return open(fout.name, "rb")


class APIUser(HttpUser):
    "Submit files for scanning"

    @task
    def run_flow(self):
        attach = random_file()
        response = self.client.post(AV_ENDPOINT, files={"file": attach})
        results = response.json()
        self.client.get(f"{AV_ENDPOINT}/{results['scan_id']}")

    def on_start(self):
        self.client.headers.update({"Authorization": os.environ.get("API_AUTH_TOKEN")})
