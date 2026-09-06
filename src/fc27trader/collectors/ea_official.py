from __future__ import annotations

import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from fc27trader.domain.enums import EvidenceClass, EventType
from fc27trader.domain.events import MarketEvent

from .base import Collector, RawObservation
from .http import PublicHttpClient


class _EAHtmlExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.h1_parts: list[str] = []
        self.paragraphs: list[str] = []
        self.all_text_parts: list[str] = []
        self._capture_h1 = 0
        self._capture_p = 0
        self._current_p: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attr_map = dict(attrs)
        if tag == "a" and attr_map.get("href"):
            self.hrefs.append(attr_map["href"])
        if tag == "h1":
            self._capture_h1 += 1
        if tag == "p":
            self._capture_p += 1
            if self._capture_p == 1:
                self._current_p = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self._capture_h1:
            self._capture_h1 -= 1
        if tag == "p" and self._capture_p:
            self._capture_p -= 1
            if self._capture_p == 0:
                text = " ".join(self._current_p).strip()
                if text:
                    self.paragraphs.append(text)
                self._current_p = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        self.all_text_parts.append(text)
        if self._capture_h1:
            self.h1_parts.append(text)
        if self._capture_p:
            self._current_p.append(text)


class EAOfficialNewsCollector(Collector):
    key = "ea_official"

    def __init__(self, index_url: str, game_year: int, http: PublicHttpClient | None = None) -> None:
        self.index_url = index_url
        self.game_year = game_year
        self.http = http or PublicHttpClient()

    def collect(self) -> list[RawObservation]:
        now = datetime.now(UTC)
        response = self.http.get(self.index_url)
        return [
            RawObservation(
                source_key=self.key,
                source_kind=f"ea_fc{self.game_year}_news_index",
                url=str(response.url),
                observed_at=now,
                body=response.content,
                status_code=response.status_code,
                content_type=response.headers.get("content-type"),
                etag=response.headers.get("etag"),
                last_modified=response.headers.get("last-modified"),
            )
        ]

    @staticmethod
    def _extract(html: bytes) -> _EAHtmlExtractor:
        parser = _EAHtmlExtractor()
        parser.feed(html.decode("utf-8", errors="replace"))
        return parser

    def discover_article_urls(self, html: bytes) -> list[str]:
        parsed_html = self._extract(html)
        urls: set[str] = set()
        game_slug = f"fc-{self.game_year}"
        for href in parsed_html.hrefs:
            absolute = urljoin(self.index_url, href)
            parsed = urlparse(absolute)
            if parsed.netloc.endswith("ea.com") and f"/{game_slug}/news/" in parsed.path:
                urls.add(absolute.split("?")[0].split("#")[0])
        return sorted(urls)

    def collect_article(self, url: str) -> RawObservation:
        now = datetime.now(UTC)
        response = self.http.get(url)
        return RawObservation(
            source_key=self.key,
            source_kind=f"ea_fc{self.game_year}_news_article",
            url=str(response.url),
            observed_at=now,
            body=response.content,
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
        )

    def parse_article_event(self, obs: RawObservation) -> MarketEvent:
        parsed_html = self._extract(obs.body)
        title = " ".join(parsed_html.h1_parts).strip() or "EA SPORTS FC announcement"
        body_text = " ".join(parsed_html.paragraphs[:8])
        full_text = " ".join(parsed_html.all_text_parts)
        date_text = self._find_date_text(full_text)
        published_at = self._parse_english_date(date_text) if date_text else None
        return MarketEvent(
            event_type=EventType.EA_ANNOUNCEMENT,
            evidence_class=EvidenceClass.CONFIRMED,
            game_year=self.game_year,
            source_key=self.key,
            external_id=obs.url,
            title=title,
            summary=body_text[:2000] or None,
            published_at=published_at,
            effective_at=published_at,
            detected_at=obs.observed_at,
            source_url=obs.url,
            payload={"date_text": date_text},
        )

    @staticmethod
    def _find_date_text(text: str) -> str | None:
        match = re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}\b",
            text,
        )
        return match.group(0) if match else None

    @staticmethod
    def _parse_english_date(value: str) -> datetime | None:
        try:
            return datetime.strptime(value, "%B %d, %Y").replace(tzinfo=UTC)
        except ValueError:
            return None
