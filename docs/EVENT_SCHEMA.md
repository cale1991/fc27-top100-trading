# Event Schema

Canonical Python contract: `fc27trader.domain.events.MarketEvent`.

```json
{
  "event_type": "sbc_released",
  "evidence_class": "confirmed",
  "game_year": 26,
  "source_key": "ea_official",
  "external_id": "provider-or-page-id",
  "title": "Event title",
  "summary": "Short normalized description",
  "published_at": "2026-09-04T17:00:00Z",
  "effective_at": "2026-09-04T17:00:00Z",
  "expires_at": null,
  "detected_at": "2026-09-04T17:00:37Z",
  "source_url": "https://...",
  "affected_card_ids": [],
  "affected_segments": ["rating:84", "league:Premier League"],
  "payload": {}
}
```

Allowed evidence classes are exactly: `confirmed`, `measured`, `model_inference`, `credible_leak`, `speculation`.

Implemented event types:
`ea_announcement`, `sbc_released`, `sbc_updated`, `sbc_expired`, `evolution_released`, `evolution_updated`, `evolution_expired`, `promo_released`, `objective_released`, `live_event_released`, `reward_changed`, `store_pack_changed`, `pack_probability_changed`, `price_range_changed`, `card_released`, `card_entered_packs`, `card_left_packs`, `gameplay_change`, `scheduled_content`, `leak`.

`content_events.event_hash` makes normalized events idempotent. `event_impacts` is the fan-out table for direct card/segment impacts. Relationship-graph traversal expands those impacts to indirect cards before reevaluation jobs are emitted.
