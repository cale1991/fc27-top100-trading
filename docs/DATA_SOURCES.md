# Data Source Map — verified 2026-09-04

## EA SPORTS FC official — automated primary content source

Use for confirmed information: announcements, promo descriptions, SBC/Evo/objective/reward descriptions when published, pack-probability methodology/pages, title updates and scheduled content.

Initial polling URLs:
- `https://www.ea.com/games/ea-sports-fc/fc-26/news`
- `https://www.ea.com/games/ea-sports-fc/fc-27/news`
- EA Help FC pages and official pack-probability page can be added as dedicated collectors.

Cadence: 120 seconds with content hashing/conditional HTTP. New/changed pages create `content_events` immediately.

## FUTBIN — manual validation only unless permission/API obtained

Useful PC price history, market list, price ranges and sales UI. Current terms state no web scraping/data mining without written permission. Do not automate it in this repository.

## FUT.GG — manual validation only unless written consent/API obtained

Excellent SBC/Evolution/card metadata. Current terms prohibit automated access/scraping and specifically prohibit using service data to train/develop/improve ML/AI without prior written consent.

## FUTWIZ — manual validation / future permission path

Provides PC market index, card prices, daily content and TradeWatch. It is an EA-approved FC Community API site, but this project has no public API/automation permission contract from FUTWIZ, so no scraper is included.

## FUT-DB — automated API, metadata + slow reference prices

Base documentation: `https://api.fut-db.com/`
- players/card metadata
- clubs/leagues/nations/rarities
- premium player prices

Provider states price refresh is roughly 30 minutes to 24 hours depending on card. Therefore use for metadata and fallback/reference prices, never as a 2-minute live feed.

## The Coin Printer — automated reference PC-price API

Documented read-only endpoint:
- `GET https://api.thecoinprinter.com/api/v1/public/players/search`
- bearer API key
- 60 requests/minute
- max `take=50`
- returns `pc_price`, `console_price`, player metadata, year and `updated_at`

Its public FAQ says prices are refreshed **multiple times per day**, so the default classification is reference/validation data, not a 2-minute live market feed. The adapter and qualification script remain useful for metadata/reference captures and for testing any higher-freshness commercial arrangement.

## EA FC Community API

EA announced July 27, 2026 that only FUT.GG, FUTBIN and FUTWIZ are authorized sites at launch. It is not a public API available to this repository, so do not reverse-engineer or impersonate an approved partner.

## Required primary 2-minute PC feed — procurement/licensing gap

No public source verified on 2026-09-04 both permits our automated/model use **and** advertises provider-side PC market freshness near 2 minutes. That prevents us from claiming a `HOT_REFERENCE` feed, but it does not block slower `REFERENCE`, `HISTORICAL`, or `METADATA` use. Fresh execution verification can come from a trusted current source or manual user observation.

## Deliberately excluded

- Unofficial EA Web App automation endpoints / account-session scraping.
- Autobuyers, autobidders, auto-listing or any transfer-market execution bot.
- Third-party "FUTBIN APIs" that are simply scraping/repackaging FUTBIN without clear rights.
