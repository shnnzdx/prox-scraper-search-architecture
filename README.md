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
