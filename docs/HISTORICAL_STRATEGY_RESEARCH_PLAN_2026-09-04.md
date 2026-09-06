# Historical Trading Strategy Research Plan — 2026-09-04

## Research rule

The goal is not to collect trading folklore. Each strategy must accumulate four distinct evidence types where obtainable:

1. **Mechanism/rule evidence** — why the market structure could produce the effect.
2. **Contemporaneous trader evidence** — what credible traders actually did before outcomes were known.
3. **Market/event evidence** — timestamped card/category prices and supply/liquidity around the event.
4. **Outcome/backtest evidence** — repeatable after-tax performance with sample size, capacity and uncertainty.

Popularity and follower count do not count as performance evidence.

## Priority 1 — FC26 first

Research current FC26 structure before older-cycle playbooks because it has the highest relevance to FC27 rehearsal.

### A. SBC/fodder/rating demand

Research first:

- fodder investing
- SBC anticipation
- rating-band relative value
- clubstock
- TOTW/SBC requirement scarcity

Sources prioritized:

- EA official FC26 content/reward/SBC/Evolution announcements
- The FUT Accountant / FUT Weekly cycle-specific discussions
- established trading organizations/guides where authorship is clear
- timestamped Reddit discussions used as observations/failure cases, never proof
- FC26 PC price/event series once collection is running

Key question: which ratings and rarities still respond to SBC demand under FC26's heavier content/reward supply, and how often anticipated catalysts fail?

### B. Supply timing / market shocks

Research:

- reward-supply buying
- content-time supply crashes
- promo panic buying
- post-promo rebound/reversion
- new-promo supply patterns
- cards leaving packs

Measure event-relative paths at 5m/15m/1h/3h/6h/24h/3d/7d and separate PC from console behavior.

### C. Execution-oriented strategies

Research:

- bidding below BIN
- undercut acquisition
- mass bidding
- lazy listing
- high-volume flipping
- high-value spread/Icon/Hero trading
- overnight/timezone effects

These must be judged on achievable fills, search effort, quantity/capacity and after-tax profit—not screenshots of one good purchase.

### D. Evolutions/substitutes/chemistry

FC24 introduced Evolutions and FC25/FC26 changed the structure further. Research:

- Evolution anticipation
- eligibility scarcity
- substitute-card effects
- chemistry/link demand
- eligibility-driven panic and decay

This group gets explicit structural-break handling because FIFA22/23 cannot directly evidence Evo behavior.

## Priority 2 — FC25 and FC24 temporal comparison

Use FC25/24 to identify mechanisms that survived into FC26 versus strategies that decayed.

Focus on:

- TOTY/promo supply selloffs and rebounds
- high-rated fodder demand failures as well as successes
- Evo-induced demand
- early-cycle meta demand and faster power creep
- untradeable/reward supply changes

Do not pool cycles until event structures are normalized.

## Priority 3 — FIFA23 and FIFA22 long-history evidence

These cycles are useful mainly for repeated mechanisms and trader behavior.

Initial credible anchors:

- Jan `GamingAlm` Bergmann, identified by kicker as a FIFA22 Top-100 FUT trader, with documented flipping and SBC-solution methods.
- TygrrFUT/FUTWIZ dated FIFA22 clubstock and TOTW investing guides.
- SebFUT interview material on SBC solutions and high-capital/Icon liquidity.
- Red Bull's FIFA22 guide documenting clustered bidding around reward/lightning-round supply.
- Rickth21 methods as self-reported trader evidence; leaderboard claims remain lower-confidence until independently verified.

Older-cycle evidence starts at a lower temporal weight and must survive FC26 remeasurement.

## Strategy-by-strategy evaluation template

For every strategy:

- define the mechanism and exact trigger without hindsight;
- define an observable entry rule;
- define realistic acquisition/fill logic;
- define exit/invalidation before testing;
- identify cards eligible at each historical timestamp without future knowledge;
- include EA tax;
- estimate position capacity and sell-through;
- compare against relevant category/market baseline;
- walk forward chronologically;
- report failed periods and catalyst failures;
- stratify by market regime/event type;
- record sample size/confidence;
- compare FC26 to older cycles for decay.

## Initial data availability status

As of this build:

- source/mechanism evidence: **started**;
- official structural-change evidence: **started**;
- FC26 PC long-history backtest dataset: **not yet sufficient in this repository**;
- strategy-specific closed shadow sample: **will accumulate from FC26 rehearsal**;
- quantitative profitability claims: **none are pre-seeded**.

The system is deliberately able to show a strategy with good source evidence and `n=0` measured results.

## Continuous research queue during FC27

1. Detect unexplained repeated residual patterns after controlling for known strategy/event features.
2. Register them as `strategy_discovery_candidates` with sample/effect/confidence.
3. Gather mechanism/source evidence.
4. Run out-of-sample validation.
5. Promote only after review and sufficient independent evidence.
6. Continuously re-evaluate existing strategies for decay.
