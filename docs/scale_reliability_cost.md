# Scale, Reliability, and Cost Strategy

## Purpose

This document explains how the scraper and search infrastructure scales to the Track A assumptions: about **5,000 active users**, **3 searches per user per day**, **6 retailers today**, and **10+ retailers planned**.

At this stage, the main risk is not raw API throughput. The main risk is allowing user searches to generate too much duplicate, expensive, and fragile refresh work.

The strategy is to keep user-facing search fast and cheap, while treating scraping as an asynchronous, deduplicated, rate-limited, and failure-isolated refresh workflow.

---

## 1. What should be preloaded nightly or weekly?

Preload data that is reusable across many users and has predictable value.

- Nightly:
  - top searched products by ZIP or store cluster,
  - popular grocery categories such as milk, eggs, bread, fruit, meat, and snacks,
  - retailer weekly deals and promotions,
  - price snapshots for high-demand products,
  - store availability for common products.
- Daily or weekly:
  - store metadata,
  - retailer location metadata,
  - stable product metadata,
  - brand/category mappings,
  - parser test fixtures from known retailer pages.

This keeps the index warm before users search and reduces on-demand scraping during peak traffic.

---

## 2. What should be triggered on demand?

On-demand refresh should run only when the value justifies the cost:

- query is long-tail or missing from the index,
- ZIP or store combination is new,
- price or promotion data is stale,
- one retailer is missing while others have fresh results,
- repeated demand appears for a product not covered by preload.

The API should not wait for this refresh to finish. It should return cached, indexed, partial, or stale-labeled results quickly, then update asynchronously.

---

## 3. How do we prevent duplicate execution?

Many users can search the same item in the same ZIP code within the same freshness window. Prevent duplicate work with a deterministic job key:

```text
sha256(retailer_id + store_id + zip_code + normalized_query + job_type + freshness_bucket)
```

Before enqueueing a refresh job, check Redis or DynamoDB for an active pending-job lock. If the lock exists, do not enqueue another job. Users share the same pending refresh.

Queue-level dedupe helps, but is not enough by itself because business freshness windows are usually longer than queue dedupe windows. Workers must remain idempotent.

---

## 4. How should caching work?

Caching should be layered by purpose:

```text
Redis / ElastiCache:
- hot search response cache
- pending-job locks
- freshness markers
- short negative cache after failures

OpenSearch:
- low-latency product search index
- retailer, ZIP, category, and price filtering

Postgres:
- normalized product, retailer, store, price, and job metadata

S3:
- raw scrape outputs for replay, debugging, and parser fixes
```

Suggested TTL policy:

```text
Search response cache: 15-60 minutes
Price and promotion fields: 6-12 hours
Base catalog snapshots: 24 hours
Store metadata: 24 hours or longer
Stable product metadata: 7 days
Negative cache after retailer failure: 10-15 minutes
```

Use stale-while-revalidate: return the best available result fast, label stale data when needed, and refresh in the background.

---

## 5. How do we keep search latency low?

Keep the request path lightweight:

```text
User request
-> normalize query and location
-> check Redis
-> query OpenSearch
-> fetch product details if needed
-> return result
-> enqueue async refresh only if stale or missing
```

The API should not scrape retailers inline. This keeps p95 latency stable even when retailers are slow or partially failing.

If data is stale, prefer:

- stale-but-labeled results,
- partial results from healthy retailers,
- visible freshness timestamps,
- and background refresh.

---

## 6. How does this scale to 5,000 users and beyond?

Initial load:

```text
5,000 users x 3 searches/day = 15,000 searches/day
```

That API volume is manageable. The harder scaling problem is refresh volume as retailer count and ZIP coverage grow.

Scale levers:

- scale API servers independently from workers,
- scale OpenSearch independently from scrape execution,
- queue per retailer or retailer family,
- enforce per-retailer concurrency limits,
- increase preload coverage for high-demand products,
- tune TTLs based on freshness complaints and hit rate,
- open circuit breakers when retailer failures spike,
- replay DLQ only after root cause is fixed.

As the platform grows from 6 to 10+ retailers, each new retailer should follow the same adapter contract: rate limit, timeout, parser, retry policy, circuit breaker, and observability labels.

---

## 7. Where should we minimize cloud spend?

Highest-cost areas are typically:

- browser-based scraping,
- proxy usage,
- repeated duplicate fetches,
- retries during retailer instability,
- preloading low-value data.

Cost controls should exist at two levels.

Application-level guardrails:

- cache-first search behavior,
- deterministic dedupe locks,
- daily scrape caps,
- per-retailer job caps,
- retry caps,
- proxy spend caps,
- browser-job approval thresholds,
- circuit breakers during failure spikes.

Cloud-level guardrails:

- AWS Budgets alerts,
- CloudWatch alarms,
- queue depth alarms,
- concurrency limits,
- S3 lifecycle rules for raw payload retention,
- autoscaling tied to queue depth and worker success rate.

The strongest cost optimization is avoiding unnecessary scraping entirely.

---

## Final Strategy

Optimize for **fast search, controlled freshness, isolated failures, and predictable cost**.

The core design choice is to treat scraping as an expensive background refresh mechanism, not as the default search path. By combining preload, TTL caching, deterministic deduplication, retailer-isolated queues, retry limits, and circuit breakers, the platform can scale without letting cost or failure rates grow uncontrollably.
