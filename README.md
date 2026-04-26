<<<<<<< HEAD
# Prox Track A: Scraper & Search Infrastructure Architecture

This repo contains an architecture-first submission for the Prox Cloud Architecture Intern technical assessment, focused on **Track A: Scraper & Search Infrastructure Architecture**.

The goal is not to build a production scraper for every retailer. The goal is to show a realistic system design for a grocery search product that can:

- return low-latency search results,
- avoid duplicate scraping work,
- refresh stale data safely,
- isolate retailer failures,
- and control infrastructure spend as usage grows.

Prox's public product positioning centers on comparing grocery prices across nearby retailers, surfacing deals, and helping users build a cheaper cart across stores near their ZIP code. That product shape drives the architecture in this repo: search must be fast, scraping must be asynchronous, and freshness must be balanced against cost.

## Deliverables

- [docs/architecture.md](/c:/Users/zdxzh/Desktop/Web%20crawler/docs/architecture.md)
- [docs/runbook.md](/c:/Users/zdxzh/Desktop/Web%20crawler/docs/runbook.md)
- [docs/scale_reliability_cost.md](/c:/Users/zdxzh/Desktop/Web%20crawler/docs/scale_reliability_cost.md)


## Recommended Submission Positioning

The strongest framing for this assessment is:

> I optimized the search path for latency and the scrape path for freshness, cost control, and failure isolation.

That framing matches the likely business reality of a product like Prox:

- many users may search the same basket or item set,
- retailer pages are slow and inconsistent,
- ZIP-code-specific data changes more often than product metadata,
- and repeated on-demand scraping is the main cost and reliability risk.

## Proposed Prototype Scope

If you decide to add a prototype later, keep it intentionally small:

- one `Search API` entry point,
- mock retailer adapters instead of live scraping,
- deterministic job deduplication,
- per-retailer queue isolation,
- retry with backoff,
- stale-while-revalidate responses,
- and basic logs / metrics counters.

This is enough to demonstrate the architecture without getting blocked by anti-bot defenses, legal ambiguity, or brittle browser automation.

## Key Tradeoffs

- `Cache-first` beats `scrape-on-every-request` because user-facing latency matters more than absolute freshness on every query.
- `Async refresh` beats `blocking refresh` because stale-but-labeled results are better than timeouts.
- `Retailer-specific queues` beat one shared queue because failure isolation is critical.
- `Business-level dedupe` matters more than queue-level dedupe alone because multiple users often trigger the same logical fetch within the freshness window.
- `Mock adapters` are the right prototype choice because the assessment is about systems thinking, not bypassing retailer protections.

## Suggested Next Step

Use the docs in this repo as your submission backbone, then only spend expensive model tokens on:

- refining wording,
- stress-testing assumptions,
- and polishing tradeoff explanations.

Do not spend most of the budget asking a model to rediscover the architecture from scratch.
=======
# Prox Track A Prototype

This repo is for the Prox Cloud Architecture Intern technical assessment, Track A: Scraper & Search Infrastructure Architecture.

It includes architecture docs plus a runnable local Python prototype that demonstrates:

- cache-first search,
- stale-while-revalidate refresh,
- deterministic dedupe,
- queue-based background refresh,
- retailer-specific mock workers,
- retry with backoff,
- and failed-job handling.

The prototype is intentionally local and lightweight. It does not scrape live sites and does not require cloud credentials.

## Project Overview

This submission focuses on the architecture and behavior of a grocery search platform, not on production scraping. The prototype shows how a cache-first search API, deduplicated refresh jobs, and mock retailer workers can support stale-while-revalidate behavior without adding cloud infrastructure or live retailer integrations.

## Assessment Track

- Track: `Scraper & Search Infrastructure Architecture`
- Focus: realistic architecture and operational behavior, not live scraping

## Architecture Summary

The design optimizes:

- search path for latency,
- refresh path for freshness and cost control.

Production equivalents are documented as AWS-native services, while prototype code uses local in-memory components and JSON files.

## Repo Layout

- [docs/architecture.md](docs/architecture.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/scale_reliability_cost.md](docs/scale_reliability_cost.md)
- `docs/prompt_diagnosis.md`
- `prompts/architecture_master_prompt.md`
- `prototype/README.md`

## Local Setup

```bash
pip install -r requirements.txt
```

Run API:

```bash
uvicorn prototype.app:app --reload
```

Run demo script in a separate terminal after the API is up:

```bash
python -m prototype.demo
```

## Example API Calls

```bash
curl -X POST http://127.0.0.1:8000/search -H "Content-Type: application/json" -d "{\"query\":\"milk\",\"zip_code\":\"90210\"}"
curl -X POST http://127.0.0.1:8000/worker/run-once
curl http://127.0.0.1:8000/jobs
curl http://127.0.0.1:8000/failed-jobs
curl http://127.0.0.1:8000/health
```

## Expected Demo Flow

1. First `/search` usually returns cache miss and enqueues refresh jobs.
2. Repeated `/search` shows cache hit or dedupe suppression.
3. `/worker/run-once` processes queued retailer jobs.
4. `/jobs` shows queue/job lifecycle.
5. `/failed-jobs` shows dead-lettered jobs after retry exhaustion.

## Mocked vs Production Equivalent

- `prototype/cache.py` in-memory TTL cache -> Redis/ElastiCache
- `prototype/job_queue.py` local queue -> SQS
- `prototype/data/mock_index.json` JSON index -> OpenSearch + Postgres
- `prototype/data/failed_jobs.json` JSON DLQ -> SQS DLQ / failure table
- `prototype/retailers/*_mock.py` mock adapters -> approved APIs/feed integrations or controlled scraping workers

## What Is Mocked

- Retailer responses are generated by local mock adapters, not by live retailer APIs or scraping.
- Queueing, cache, and dedupe are implemented in memory for local demonstration.
- Search/index persistence is stored in local JSON files under `prototype/data`.
>>>>>>> 475eb6b (Initial Track A prototype submission)
