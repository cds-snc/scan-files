# Scan Files 🖨️

_La version française sera disponible bientôt_

This repository is for a file scanning product for CDS Platform applications.

## API docs
- https://scan-files.alpha.canada.ca/docs

## Supported scanners:
- [Assemblyline](https://cybercentrecanada.github.io/assemblyline4_docs/)
- [ClamAV](https://www.clamav.net/)

## Modules
- [S3 scan object](./module/s3-scan-object/)

# Development
Recommended: `devcontainer` extension for VSCode

To bring up your local dev environment, make sure you have install the requirements & run migrations:
```
make install
make install-dev
make migrations
```

Bring up the local dev environment:
```
make dev
```

## Load testing
The API contains a `locust` file to test a basic workflow:

1. Upload file
2. Check for results

Ensure that the `API_AUTH_TOKEN` environment variable is set before running load tests

You can start it by running `make load-test` in the `api` directory and the visiting: `http://localhost:8089/`. The URL to perform load tests against is https://scan-files.alpha.canada.ca.
