# Prototype Guide

This folder contains a local runnable prototype for Track A.

## What It Demonstrates

- cache-first search behavior,
- stale-while-revalidate refresh,
- deterministic dedupe with lock TTL,
- queue-based refresh jobs,
- retailer-specific mock adapters,
- retry with exponential backoff,
- failed-job handling via local JSON file,
- structured JSON-style logs.

## Start API

```bash
uvicorn prototype.app:app --reload
```

## Try Manually

```bash
curl -X POST http://127.0.0.1:8000/search -H "Content-Type: application/json" -d "{\"query\":\"milk\",\"zip_code\":\"90210\"}"
curl -X POST http://127.0.0.1:8000/worker/run-once
curl http://127.0.0.1:8000/jobs
curl http://127.0.0.1:8000/failed-jobs
```

## Demo Script

```bash
python -m prototype.demo
```

Run the demo script after the API is running.

