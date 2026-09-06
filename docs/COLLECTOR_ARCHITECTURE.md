# Collector Architecture

Collection is role-aware and attention-aware.

- Content collectors run continuously.
- Reference providers run at the fastest cadence their rights, rate limits and actual data freshness justify.
- `HOT_REFERENCE` providers may support <=300-second reference observations but are optional.
- Broad discovery operates over all practically observable PC cards from available legal sources.
- Candidate/position/catalyst cards receive increased observation effort through expiring `attention_allocations`.
- Cards that lose opportunity value are automatically deprioritized and may later re-enter.

`collection_targets` is scheduler state, not a permanent watchlist.

Current nominal attention tiers are 120s / 300s / 900s, but provider-side data freshness is always stored separately from request cadence.
