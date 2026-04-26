# Scale, Reliability, and Cost Strategy

## Purpose

This document explains how the scraper and search infrastructure scales to the initial Prox assessment assumptions: about **5,000 active users**, **3 searches per user per day**, **6 retailers today**, and **10+ retailers planned**. At this scale, the main risk is not raw API throughput. The main risk is letting user searches create too many duplicate, expensive, and fragile retailer refresh jobs.

The strategy is to keep user-facing search fast and cheap, while treating scraping as an asynchronous, deduplicated, rate-limited, and failure-isolated refresh workflow.

---

## 1. What should be preloaded nightly or weekly?

Preload data that is reusable across many users and has predictable value:

- **Nightly**
  - top searched products by ZIP/store cluster,
  - popular grocery categories such as milk, eggs, bread, fruit, meat, and snacks,
  - retailer weekly deals and promotions,
  - price snapshots for high-demand products,
  - store availability for common products.

- **Daily or weekly**
  - store metadata,
  - retailer location metadata,
  - stable product metadata,
  - brand/category mappings,
  - parser test fixtures from known retailer pages.

This keeps the search index warm before users search. It also reduces on-demand scraping during peak traffic.

---

## 2. What should be triggered on demand?

On-demand refresh should be used only when the value justifies the cost:

- a query is long-tail or missing from the index,
- a ZIP/store combination has not been seen before,
- price or promotion data is stale,
- one retailer has missing results while others have fresh results,
- or a user search indicates repeated demand for a product not covered by preload.

The API should not wait for this refresh to finish. It should return cached, indexed, partial, or stale-labeled results immediately, then update data asynchronously.

---

## 3. How do we prevent duplicate execution?

Many users may search for the same item in the same ZIP code within the same freshness window. The system prevents duplicate work with a deterministic job key:

```text
sha256(retailer_id + store_id + zip_code + normalized_query + job_type + freshness_bucket)
```

Before enqueueing a scrape job, the API or scheduler checks Redis/DynamoDB for an active pending-job lock. If the lock already exists, the system does not enqueue another job. Users share the same pending refresh and receive the best currently available result.

Queue-level deduplication can help, but it is not enough by itself because business freshness windows are usually longer than queue deduplication windows. Workers must still be idempotent so duplicate messages do not create duplicate writes.

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
Search response cache: 15–60 minutes
Price and promotion fields: 6–12 hours
Base catalog snapshots: 24 hours
Store metadata: 24 hours or longer
Stable product metadata: 7 days
Negative cache after retailer failure: 10–15 minutes
```

The system should use **stale-while-revalidate**: return the best available result quickly, label stale data when needed, and refresh in the background.

---

## 5. How do we keep search latency low?

The user-facing request path should avoid expensive work:

```text
User request
→ normalize query and location
→ check Redis
→ query OpenSearch
→ fetch product details if needed
→ return result
→ enqueue async refresh only if stale or missing
```

The API should never perform retailer scraping inline. This keeps p95 latency stable even when retailers are slow, blocked, or partially unavailable.

If data is stale, the system should prefer:

- returning stale-but-labeled results,
- returning partial results from healthy retailers,
- showing freshness timestamps,
- and refreshing asynchronously.

This is better than making the user wait for live scraping.

---

## 6. How does this scale to 5,000 users and beyond?

The initial load is about:

```text
5,000 users × 3 searches/day = 15,000 searches/day
```

That volume is manageable for an API and search index. The harder scaling problem is controlling refresh work as retailer count and ZIP coverage grow.

Scaling levers:

- scale API servers separately from workers,
- scale OpenSearch independently from the scrape system,
- add queues per retailer or retailer family,
- apply per-retailer concurrency limits,
- increase preload coverage for high-demand products,
- tune TTLs based on freshness complaints and cache hit rate,
- use circuit breakers when retailer failure rates spike,
- and replay failed jobs from DLQ only after the root cause is fixed.

As the platform grows from 6 retailers to 10+ retailers, each new retailer should be added through the same adapter pattern: rate limit, timeout, parser, retry policy, circuit breaker, and observability labels.

---

## 7. Where should we minimize cloud spend?

The highest-cost areas are likely:

- browser-based scraping,
- proxy usage,
- repeated duplicate fetches,
- retries during retailer instability,
- and over-preloading low-value data.

Cost controls should exist at two levels.

### Application-level guardrails

- cache-first search behavior,
- deterministic dedupe locks,
- daily scrape caps,
- per-retailer job caps,
- retry caps,
- proxy spend caps,
- browser-job approval thresholds,
- and circuit breakers during failure spikes.

These controls prevent runaway spend before the cloud bill grows.

### Cloud-level guardrails

- AWS Budgets alerts,
- CloudWatch alarms,
- queue-depth alarms,
- concurrency limits,
- S3 lifecycle rules for raw payload retention,
- and autoscaling policies based on queue depth and worker success rate.

The best cost optimization is not choosing the cheapest compute instance. It is avoiding unnecessary scraping entirely.

---

## Final Strategy

The system should optimize for **fast search, controlled freshness, isolated failures, and predictable cost**.

The strongest design choice is to treat scraping as an expensive background refresh mechanism, not as the default search path. By combining scheduled preload, TTL caching, deterministic deduplication, retailer-specific queues, retry limits, and circuit breakers, the platform can support the initial 5,000-user load and scale to more users and retailers without letting cost or failure rates grow uncontrollably.

