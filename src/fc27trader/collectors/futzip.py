from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Iterable

from fc27trader.collectors.base import Collector, RawObservation
from fc27trader.collectors.http import ConditionalState, PublicHttpClient

FUTZIP_FEEDS = {
    "movers": "https://futzip.com/feed/movers.xml",
    "new": "https://futzip.com/feed/new.xml",
    "sbc": "https://futzip.com/feed/sbc.xml",
}
PARSER_VERSION = "futzip-rss-v1"
SCHEMA_VERSION = "1"

_MOVE_RE = re.compile(
    r"^(?P<name>.+?)\s+(?P<rating>\d{2,3})\s+(?P<pct>[+-]?\d+(?:\.\d+)?)%:\s*"
    r"(?P<old>[\d,]+)\s*[→>-]+\s*(?P<new>[\d,]+)\s*$"
)
_PLAYER_ID_RE = re.compile(r"/player/(?P<id>\d+)(?:/|$)")
_RATING_RE = re.compile(r"(?:^|\s)(?P<rating>\d{2,3})(?:\s|$)")


@dataclass(slots=True)
class FutzipItem:
    feed_key: str
    guid: str
    title: str
    link: str | None
    description: str | None
    provider_timestamp: datetime | None
    provider_card_id: str | None
    player_name: str | None = None
    rating: int | None = None
    old_price: int | None = None
    new_price: int | None = None
    percentage_change: float | None = None
    raw_xml: str = ""
    parse_error: str | None = None


class FutzipCollector(Collector):
    """Public FUTZIP RSS collector.

    The RSS mover feed does not establish platform identity in its item schema/public
    feed documentation. Parsed price changes are therefore MARKET_CONTEXT/UNKNOWN,
    never executable or PC reference prices.
    """

    key = "futzip"

    def __init__(self, *, http: PublicHttpClient | None = None) -> None:
        self.http = http or PublicHttpClient(timeout_seconds=15.0, max_attempts=3)

    def collect(self) -> list[RawObservation]:
        return self.collect_feed("movers")

    def collect_feed(self, feed_key: str, state: ConditionalState | None = None) -> list[RawObservation]:
        if feed_key not in FUTZIP_FEEDS:
            raise ValueError(f"unsupported FUTZIP feed: {feed_key}")
        url = FUTZIP_FEEDS[feed_key]
        response = self.http.get(url, state=state)
        now = datetime.now(UTC)
        return [RawObservation(
            source_key=self.key,
            source_kind=f"futzip_{feed_key}_rss",
            url=url,
            observed_at=now,
            body=response.content,
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
            metadata={
                "feed_key": feed_key,
                "parser_version": PARSER_VERSION,
                "schema_version": SCHEMA_VERSION,
                "observation_semantics": "MARKET_CONTEXT" if feed_key == "movers" else "CONTENT_EVENT",
                "market_segment": "UNKNOWN",
            },
        )]


def _text(node: ET.Element, tag: str) -> str | None:
    child = node.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _parse_pubdate(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None


def parse_futzip_rss(body: bytes, feed_key: str) -> tuple[list[FutzipItem], list[dict]]:
    """Parse items independently so one malformed item never discards the feed."""
    if feed_key not in FUTZIP_FEEDS:
        raise ValueError(f"unsupported FUTZIP feed: {feed_key}")
    root = ET.fromstring(body)
    items: list[FutzipItem] = []
    failures: list[dict] = []
    for index, node in enumerate(root.findall(".//item")):
        raw_xml = ET.tostring(node, encoding="unicode")
        try:
            title = _text(node, "title") or ""
            link = _text(node, "link")
            guid = _text(node, "guid")
            if not guid:
                raise ValueError("RSS item missing guid")
            description = _text(node, "description")
            pub = _parse_pubdate(_text(node, "pubDate"))
            provider_card_id = None
            if link:
                match = _PLAYER_ID_RE.search(link)
                provider_card_id = match.group("id") if match else None

            parsed = FutzipItem(
                feed_key=feed_key,
                guid=guid,
                title=title,
                link=link,
                description=description,
                provider_timestamp=pub,
                provider_card_id=provider_card_id,
                raw_xml=raw_xml,
            )
            if feed_key == "movers":
                match = _MOVE_RE.match(title)
                if not match:
                    raise ValueError(f"unrecognized mover title: {title!r}")
                parsed.player_name = match.group("name").strip()
                parsed.rating = int(match.group("rating"))
                parsed.old_price = int(match.group("old").replace(",", ""))
                parsed.new_price = int(match.group("new").replace(",", ""))
                parsed.percentage_change = float(match.group("pct"))
            elif feed_key == "new":
                # Keep extraction conservative. Stable provider ID is authoritative for
                # the FUTZIP identity; name/rating are descriptive only until mapped.
                title_without_action = re.split(r"\s+(?:added|detected|new card|is now live)\b", title, flags=re.I)[0].strip()
                rating_match = list(_RATING_RE.finditer(title_without_action))
                if rating_match:
                    last = rating_match[-1]
                    parsed.rating = int(last.group("rating"))
                    parsed.player_name = (title_without_action[: last.start()] + title_without_action[last.end() :]).strip(" -–—:") or None
                else:
                    parsed.player_name = title_without_action or None
            else:
                parsed.player_name = None
            items.append(parsed)
        except Exception as exc:  # item-level isolation is deliberate
            failures.append({"index": index, "error": str(exc), "raw_xml": raw_xml})
    return items, failures
