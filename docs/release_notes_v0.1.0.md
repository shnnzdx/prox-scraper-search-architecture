# Release Notes - v0.1.0

Date: 2026-04-26

## Highlights

This release delivers a complete Track A prototype package for the Prox Cloud Architecture Intern technical assessment:

- clear architecture documentation,
- operational runbook,
- scale, reliability, and cost strategy,
- and a runnable local prototype that demonstrates cache-first search plus asynchronous refresh.

## What Is Included

### Documentation

- Architecture design focused on latency, freshness, failure isolation, and cost control.
- Runbook covering deployment checks, monitoring, and incident response.
- Strategy document for preload vs on-demand refresh and dedupe-driven cost control.

### Prototype

- FastAPI search endpoint and worker endpoint.
- In-memory TTL cache.
- Deterministic dedupe lock model.
- Queue-based refresh jobs.
- Mock retailer adapters with different latency and failure characteristics.
- Retry and failed-job handling.

### Reliability and Demo Polish

- Cache behavior aligned with refresh lifecycle.
- Cache-hit responses explicitly avoid claiming new enqueue activity.
- Worker failure path includes structured logging.
- Freshness checks handle invalid timestamps defensively.
- Demo flow shows post-worker search behavior.

## Notes for Reviewers

- This is intentionally a lightweight local prototype.
- No live retailer scraping is included.
- No heavy infrastructure dependencies are required for local execution.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn prototype.app:app --reload
python -m prototype.demo
```
