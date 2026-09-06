# FC26 Provider Capability & Rights Audit — 2026-09-04

Checked 2026-09-04. This is an integration/rights audit, not a claim that every source has produced a successful runtime response in this build environment. Automation rights, private storage/derived use, commercial use, redistribution, and SaaS display are tracked separately.

## Tier A — immediately usable automated sources

### FUTZIP — PUBLIC_FEED
- **FC26:** yes. Public RSS endpoints documented for market movers, new cards, and SBCs.
- **Market semantics:** FUTZIP states it tracks PC and console separately on its service, but the public RSS mover items audited here do not encode platform. RSS mover events therefore normalize to `UNKNOWN / MARKET_CONTEXT`, never PC/console/Switch reference price or execution truth.
- **IDs/timestamps:** stable player IDs in player URLs; GUID + publication timestamps in RSS.
- **Cadence:** project polls each feed every 5 minutes, conditionally using ETag/Last-Modified when supplied.
- **Rights:** automated RSS consumption is explicitly intended by the feed page. Persistent/private storage is used for provenance; commercial redistribution/SaaS rights are not assumed.
- **Sources:** https://futzip.com/feeds · https://futzip.com/method · https://futzip.com/

### EA official — PUBLIC_CONTENT
- Authoritative content/context: announcements, promos, rules, updates, events and published probabilities where available.
- Not market-price or execution data.
- The FC Community API is partner-restricted and is not assumed available to this project.
- Sources: https://www.ea.com/games/ea-sports-fc/fc-26/news · https://www.ea.com/games/ea-sports-fc/fc-26/news/pitch-notes-fc26-community-api-update

## Tier B — optional structured sources requiring credentials/payment/access

### Parse.bot FUTBIN wrapper — OPTIONAL_STRUCTURED_PROVIDER
- **Relationship:** Parse's documented authenticated commercial REST wrapper; independent/unofficial relative to FUTBIN. It is not labelled an official FUTBIN developer API.
- **Implemented:** optional `ParseBotFutbinCollector`, disabled by default. `PARSE_FUTBIN_ENABLED=true` + `PARSE_API_KEY` required.
- **Capabilities audited:** FC26 catalogue/search, stable FUTBIN IDs, player detail, stats/PlayStyles, `price_pc`, `price_ps`, market trends/index samples, SBCs, Evolutions, objectives.
- **Semantics:** `price_pc` → PC `REFERENCE_PRICE`; `price_ps` → provider-labelled `PLAYSTATION` `REFERENCE_PRICE`. It is **not** reinterpreted as Xbox/shared-console. Neither field can create/overwrite an execution observation or Portfolio executable mark.
- **History:** no full player-level historical-price endpoint was established in the documented wrapper; do not invent one.
- **Economics:** roughly 30 catalogue rows/page and 1 credit/successful call on the audited wrapper. Using ~28.5k cards only as a universe-scale planning estimate implies ~950 calls/full catalogue pass. Full-universe high-frequency polling is deliberately not implemented.
- **Collection modes:** `CATALOGUE_BOOTSTRAP`, `METADATA_REFRESH`, `HOT_SET`, `WATCH_SET`, `EVENT_TRIGGERED`, `ON_DEMAND`. Deterministic hot-set prioritization protects credits.
- **Current Parse plans checked:** Free 200 credits/5 rpm; Hobby $30/1,000/20 rpm; Developer $100/5,000/100 rpm; Team $300/20,000/300 rpm; Company $1,000/100,000/500 rpm. Plans can change and should be rechecked before purchase.
- **Rights/risk:** private integration consumes Parse's documented commercial API rather than implementing a FUTBIN scraper. Upstream relationship/availability, persistent-storage/derived-use rights and any future commercial/SaaS redistribution rights remain vendor/upstream risks to revalidate. No provider is a critical dependency.
- **Sources:** https://parse.bot/marketplace/1b6234f9-0dfb-4cca-99b4-2d6d37aec6a7/futbin-com-api · https://parse.bot/pricing · https://www.futbin.com/tos

### FUT-DB — DOCUMENTED_API / TRIAL_PENDING
- FC26 catalogue, metadata, stats, stable IDs and price endpoints are documented.
- Vacation-PC runtime verification: configured key returned HTTP 429 with `x-ratelimit-limit=0`, `x-ratelimit-remaining=0`; project maps this to `NO_QUOTA` and backs off instead of hammering.
- Current public Premium listing checked: €79/month, 20,000 requests/day. Published price freshness varies materially by card (roughly 30 minutes–24 hours), so it is reference/history, not execution truth.
- Source: https://fut-db.com/

### The Coin Printer — DOCUMENTED_API / APPROVAL_REQUIRED
- Read-only partner API with player metadata, `pc_price`, provider-defined `console_price`, `updated_at`, stable IDs; documented rate limit 60 req/min.
- `pc_price` → PC reference. `console_price` → `CONSOLE_GENERIC` unless provider/title documentation proves a more specific canonical market.
- Key/payment/approval required; no key configured. Private storage/model/commercial rights should be confirmed with the purchased agreement.
- Source: https://www.thecoinprinter.com/docs

## Tier C — manual/research reference

### FUTBIN direct — MANUAL_REFERENCE
High-value human reference surface, but no public developer market-data API was established. The project does not scrape it automatically. Current Terms include a no-scraping/data-mining provision absent permission and separate business-use licensing conditions. Source: https://www.futbin.com/tos

### FUT.GG — RESEARCH_REFERENCE
Useful metadata/prices/SBC/Evolution surface, but no approved public market-data ingestion route for this project was established. Current terms reviewed in this phase restrict automated access except where permitted and separately restrict ML use without consent. No collector. Source: https://www.fut.gg/terms

### FUTWIZ — RESEARCH_REFERENCE
Public FC26 PC and console market views make it useful for human validation, but no documented public server-side market-data API/automation permission was established. No collector until a legitimate API/provider agreement exists. Source: https://www.futwiz.com/

### FUTNext / FC Enhancer — RESEARCH_REFERENCE
Potential technical signal source retained for research only. No sufficiently documented server-ingestion/licensing contract, source timestamp SLA, or independently established provenance was found. No production collector.

## Tier D — unsuitable for this project

### EA Web/Companion internal Transfer Market endpoints
Not a public data-provider integration and outside the manual-execution boundary. No auto-buy/sell, Web App botting, CAPTCHA bypass, anti-detection or rate-limit evasion.

## Integration priority
1. FUTZIP public event/context feeds — running independently.
2. EA official content — running independently.
3. Parse/FUTBIN optional structured provider — enable selectively if the user supplies a Parse key and accepts vendor credit costs.
4. The Coin Printer — activate if approved/keyed.
5. FUT-DB — retain and reactivate automatically when trial/Premium quota is non-zero.
6. FUTWIZ/FUTBIN direct/FUT.GG/FUTNext — manual/research until a legitimate automated route exists.

No single third-party provider is required for startup, portfolio accounting, manual execution observations, or application access.
