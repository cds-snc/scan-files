# Scan Files 🖨️

_La version française sera disponible bientôt_

This repository is for a file scanning product for CDS Platform applications.

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

# API docs

## Version

<a id="opIdversion_version_get"></a>

> Code samples

```http
GET /version HTTP/1.1

Accept: application/json

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/version', headers = headers)

print(r.json())

```

`GET /version`

*Version*

> Example responses

> 200 Response

```json
{"version":"e7d2559c834521a75695dd39f39f655d1d6eab5e"}
```

<h3 id="version_version_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

<h3 id="version_version_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## Healthcheck

<a id="opIdhealthcheck_healthcheck_get"></a>

> Code samples

```http
GET /healthcheck HTTP/1.1

Accept: application/json

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/healthcheck', headers = headers)

print(r.json())

```

`GET /healthcheck`

*Healthcheck*

> Example responses

> 200 Response

```json
{"database":{"able_to_connect":true,"db_version":"123456789"}}
```

<h3 id="healthcheck_healthcheck_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

<h3 id="healthcheck_healthcheck_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>
  
## Submit file for scanning

<a id="opIdstart_assemblyline_scan_assemblyline_post"></a>

> Code samples

```http
POST /assemblyline HTTP/1.1

Content-Type: multipart/form-data
Accept: application/json
Authorization: API_KEY

```

```python
import requests
headers = {
  'Content-Type': 'multipart/form-data',
  'Accept': 'application/json',
  'Authorization': 'API_KEY'
}

r = requests.post('/assemblyline', headers = headers)

print(r.json())

```

`POST /assemblyline`

*Start Assemblyline Scan*

> Body parameter

```yaml
file: File

```

> Example responses

> 200 Response

```json
{
    "status": "OK",
    "scan_id": "0650b3ff-65c5-4756-b5c6-6f03b7738bc9"
}
```

<h3 id="start_assemblyline_scan_assemblyline_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="start_assemblyline_scan_assemblyline_post-responseschema">Response Schema</h3>

<aside class="success">
This operation requires an API key
</aside>

## Get file scan results

<a id="opIdget_assemblyline_scan_results_assemblyline__scan_id__get"></a>

> Code samples

```http
GET /assemblyline/{scan_id} HTTP/1.1

Accept: application/json
Authorization: API_KEY

```

```python
import requests
headers = {
  'Accept': 'application/json',
  'Authorization': 'API_KEY'
}

r = requests.get('/assemblyline/{scan_id}', headers = headers)

print(r.json())

```

`GET /assemblyline/{scan_id}`

*Get Assemblyline Scan Results*

<h3 id="get_assemblyline_scan_results_assemblyline__scan_id__get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|scan_id|path|string(uuid)|true|none|

> Example responses

> 200 Response

```json
{
    "status": "in_progress"
}
```

<h3 id="get_assemblyline_scan_results_assemblyline__scan_id__get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="get_assemblyline_scan_results_assemblyline__scan_id__get-responseschema">Response Schema</h3>

<aside class="success">
This operation requires an API key
</aside>
