from datetime import UTC, datetime

from fc27trader.collectors.base import RawObservation
from fc27trader.collectors.ea_official import EAOfficialNewsCollector


def test_ea_html_parser_discovers_and_parses_article():
    c = EAOfficialNewsCollector("https://www.ea.com/games/ea-sports-fc/fc-26/news", 26)
    index = b'<a href="/games/ea-sports-fc/fc-26/news/test-promo">Promo</a>'
    assert c.discover_article_urls(index) == [
        "https://www.ea.com/games/ea-sports-fc/fc-26/news/test-promo"
    ]
    obs = RawObservation(
        source_key="ea_official",
        source_kind="article",
        url="https://www.ea.com/games/ea-sports-fc/fc-26/news/test-promo",
        observed_at=datetime.now(UTC),
        body=b"<h1>Test Promo</h1><p>September 4, 2026</p><p>New SBC content.</p>",
    )
    event = c.parse_article_event(obs)
    assert event.title == "Test Promo"
    assert event.published_at.year == 2026
