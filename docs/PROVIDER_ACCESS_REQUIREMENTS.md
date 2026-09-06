# Hot-market data-feed access requirements

Send the same technical requirements to FUTNext, FUTWIZ and FUTBIN so offers can be compared directly.

Required answers before integration:

1. Is automated server-to-server retrieval of FC26/FC27 Ultimate Team PC market prices permitted?
2. May retrieved price data be stored historically in our private database?
3. May it be used for private analytics and machine-learning model training/inference?
4. Is there a documented API/feed, authentication method and rate limit?
5. Does each price record include an authoritative `updated_at` / source timestamp?
6. What is the guaranteed or typical **data freshness**, separately from HTTP/API request rate?
7. Can >=50 cards be requested in bulk? If not, what are per-minute/day quotas?
8. Are PC prices a distinct transfer market, not a console-derived estimate?
9. Which fields are available: lowest BIN, bids, listing count, sold prices/sales velocity, price range, active auctions, historical prices?
10. Are there restrictions on polling every 2 minutes for hot cards and every 5–15 minutes for broader cards?
11. Pricing for the required volume, and whether a trial/API key can be issued for a 50-card qualification test.
12. Any retention, attribution, redistribution or derived-data restrictions.

Qualification test requested from provider:

- 50 fixed FC26 cards across fodder/meta gold/Icon-Hero/promo
- compare PC price against time-matched FUTBIN PC observations
- retain request start/end, provider timestamp and raw response reference
- compute p50/p95 provider age, p50/p95 HTTP latency, median/p90 absolute percentage price error
- reject hot-feed use if effective staleness exceeds 300 seconds

13. Identify the upstream source/provenance of the PC prices. If the feed is derived from FUTBIN, FUT.GG, FUTWIZ, EA transfer-market queries, or another vendor, disclose that dependency so the fallback can be genuinely independent.
