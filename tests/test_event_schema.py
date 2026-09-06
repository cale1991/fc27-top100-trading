from datetime import UTC, datetime

from fc27trader.domain.enums import EvidenceClass, EventType
from fc27trader.domain.events import MarketEvent


def test_event_schema_keeps_evidence_class_explicit():
    event = MarketEvent(
        event_type=EventType.SBC_RELEASED,
        evidence_class=EvidenceClass.CONFIRMED,
        game_year=26,
        source_key="ea_official",
        title="Example SBC",
        detected_at=datetime.now(UTC),
    )
    assert event.evidence_class is EvidenceClass.CONFIRMED
