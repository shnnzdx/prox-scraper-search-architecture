You are working in my GitHub repo for a Cloud Architecture Intern technical assessment.

## Mission
Build a small, runnable local prototype for Track A: Scraper & Search Infrastructure Architecture.

This is an architecture demo, not a real scraper. Keep implementation aligned with:
- docs/architecture.md
- docs/runbook.md
- docs/scale_reliability_cost.md

Read these docs first.

## Hard Constraints
1. Do NOT scrape live retailer websites.
2. Do NOT add real credentials, proxy keys, or AWS credentials.
3. Do NOT overbuild with Docker, Redis, SQS, OpenSearch, or AWS services in code.
4. Use local Python data structures + JSON files.
5. Keep it interview-friendly: clear, minimal, readable.

## Work Order
1. Fix Markdown formatting issues only if present in docs (for example accidental fenced prose blocks). Do not rewrite docs.
2. Implement the prototype.
3. Update READMEs and requirements.
4. Verify acceptance flow.
5. Return concise changed-file summary.

## Expected Structure
prototype/
  app.py
  models.py
  cache.py
  dedupe.py
  job_queue.py
  worker.py
  logger.py
  demo.py
  retailers/
    __init__.py
    base.py
    walmart_mock.py
    target_mock.py
    kroger_mock.py
  data/
    failed_jobs.json
    mock_index.json
  README.md

Also create or update:
- requirements.txt
- README.md

## Functional Requirements

### 1) API
In `prototype/app.py` create FastAPI endpoints:
- `POST /search`
- `GET /health`
- `GET /jobs`
- `GET /failed-jobs`
- `POST /worker/run-once`

`POST /search` request:
```json
{
  "query": "milk",
  "zip_code": "90210"
}
```

`POST /search` response fields:
```json
{
  "query": "milk",
  "zip_code": "90210",
  "freshness_status": "fresh | stale | partial | unavailable",
  "cache_hit": true,
  "refresh_enqueued": false,
  "dedupe_suppressed_jobs": 0,
  "results": [],
  "missing_retailers": [],
  "message": ""
}
```

### 2) Cache-First + SWR
Implement in-memory TTL cache in `prototype/cache.py`.
- Cache key includes normalized query + zip.
- Miss -> read mock index.
- Missing/stale -> enqueue refresh jobs.
- Repeat same search -> cache hit or dedupe suppression.

### 3) Mock Index
`prototype/data/mock_index.json` simulates indexed data.
Include sample entries:
- milk / 90210
- eggs / 60614
- bread / 10001

### 4) Deterministic Dedupe
In `prototype/dedupe.py` generate:
```text
sha256(retailer_id + store_id + zip_code + normalized_query + job_type + freshness_bucket)
```
Use in-memory lock registry with TTL.
Suppress duplicate enqueue while lock is active.
Return suppressed count in API response.

### 5) Queue
In `prototype/job_queue.py` implement local in-memory queue.
Each job includes:
- job_id
- job_key
- retailer_id
- query
- zip_code
- store_id
- job_type
- status
- retry_count
- created_at
- updated_at

### 6) Retailer Adapters
Create base adapter in `prototype/retailers/base.py` with `search(query, zip_code)`.
Create mock adapters:
- Walmart: low latency, low failure
- Target: medium latency, medium failure
- Kroger: higher latency, higher failure

Return mock results only.

### 7) Worker + Retry + DLQ
In `prototype/worker.py`:
- Process queued jobs.
- Respect per-retailer concurrency limits conceptually.
- Retry transient failures with short exponential backoff.
- Example sequence: immediate, short delay, longer delay, final failure.
- On retry exhaustion, append to `prototype/data/failed_jobs.json`.
- On success, update mock index and/or cache.

### 8) Structured Logging
In `prototype/logger.py` print JSON-style logs for:
- request_received
- cache_hit
- cache_miss
- index_hit
- index_miss
- refresh_enqueued
- dedupe_suppressed
- worker_job_started
- worker_job_succeeded
- worker_job_failed
- worker_retrying
- job_dead_lettered

Include fields when available:
- request_id
- job_id
- job_key
- retailer_id
- query
- zip_code
- retry_count
- duration_ms
- status
- error

### 9) Documentation
Root `README.md` must include:
- project overview
- assessment track
- architecture summary
- local setup
- install/run steps
- curl examples
- expected demo flow
- mocked vs production equivalents
- links to docs

Create `prototype/README.md` with prototype-specific usage.

### 10) Dependencies
`requirements.txt` should stay minimal, likely:
- fastapi
- uvicorn
- pydantic
- python-dotenv

Avoid heavy extras.

### 11) Demo Script
Create `prototype/demo.py` that demonstrates:
1. Search milk/90210 (cache miss expected)
2. Refresh jobs enqueued
3. Repeat same search (cache hit or dedupe suppression)
4. Run worker once or multiple times
5. Show success/failure logs
6. Show failed_jobs content if failures occur

## Acceptance Flow
Must run:
```bash
pip install -r requirements.txt
uvicorn prototype.app:app --reload
```

Manual checks:
```bash
curl -X POST http://127.0.0.1:8000/search -H "Content-Type: application/json" -d "{\"query\":\"milk\",\"zip_code\":\"90210\"}"
curl -X POST http://127.0.0.1:8000/worker/run-once
curl http://127.0.0.1:8000/jobs
curl http://127.0.0.1:8000/failed-jobs
```

The demo must clearly show:
- cache-first search
- stale-while-revalidate behavior
- deterministic dedupe
- queued refresh
- retailer-specific mock workers
- retry with backoff
- failed-job handling
- structured logs

At the end, provide a concise summary of changed files and key behavior.
