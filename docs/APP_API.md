# Application API (first usable milestone)

Main routes:

- `GET /health`
- `GET /dashboard`
- `GET /opportunities`
- `GET /opportunities/{candidate_id}`
- `GET /market/search?q=...`
- `GET /market/cards/{card_id}`
- `GET /manual-verifications/pending`
- `POST /manual-verifications/{request_id}/response`
- `POST /manual-verifications/{request_id}/evidence` (multipart screenshot/listings)
- `GET /portfolio`
- `PUT /portfolio/balance`
- `POST /portfolio/purchases`
- `POST /portfolio/sales`
- `GET /activity`
- `GET /activity/notifications`
- `GET /community`
- `GET /system`
- `WS /ws/live`

The normal user interface is the PWA, not these raw endpoints.

## Portfolio executable-mark patch (2026-09-04)

`GET /portfolio` keeps executable market evidence and reference/fair-value anchors separate for every open position. `current_liquidation_profit_after_tax` is calculated only from `current_lowest_bin` in the latest execution observation. A reference price is never substituted when the executable mark is unavailable.

`PUT /portfolio/positions/{position_id}/desired-listing-price`

```json
{"desired_listing_price": 101000}
```

Set the value to `null` to clear it. The portfolio response exposes the persisted desired listing price and its projected after-tax P/L.

Manual verification confidence and trade/model confidence are separate concepts. Verification responses expose both `execution_observation_confidence` and `trade_model_confidence` when available.
