from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import AccountMarketAccess, MarketSegment, TradingAccount
from fc27trader.domain.enums import MarketSegmentKey


FC26_SEGMENTS = (
    dict(segment_key=MarketSegmentKey.PC.value, display_name="PC", platform="pc", platform_group="pc", executable_by_user=True,
         notes="Current user's FC26 execution market."),
    dict(segment_key=MarketSegmentKey.PLAYSTATION.value, display_name="PlayStation (provider-labelled)", platform="playstation", platform_group="playstation_provider", executable_by_user=False,
         notes="Use only when a provider explicitly labels a value as PlayStation/PS. Do not reinterpret as Xbox/shared console."),
    dict(segment_key=MarketSegmentKey.CONSOLE_GENERIC.value, display_name="Console (provider-defined)", platform="console", platform_group="console_provider", executable_by_user=False,
         notes="Provider says console but does not prove a more specific/shared canonical market."),
    dict(segment_key=MarketSegmentKey.CONSOLE_SHARED.value, display_name="Shared console market", platform="console", platform_group="console_shared", executable_by_user=False,
         notes="Assign only when the title/provider explicitly establishes a shared console market."),
    dict(segment_key=MarketSegmentKey.SWITCH.value, display_name="Switch", platform="switch", platform_group="switch", executable_by_user=False,
         notes="Nintendo Switch market when explicitly identified by a provider."),
    dict(segment_key=MarketSegmentKey.UNKNOWN.value, display_name="Unknown / unspecified", platform="unknown", platform_group="unknown", executable_by_user=False,
         notes="Provider did not establish market/platform identity. Must never enter market-specific consensus."),
)


def ensure_market_segments(session: Session, *, game_year: int = 26) -> dict[str, MarketSegment]:
    definitions = FC26_SEGMENTS if game_year == 26 else tuple(
        {**spec, "executable_by_user": False, "notes": spec.get("notes")} for spec in FC26_SEGMENTS
    )
    rows: dict[str, MarketSegment] = {}
    for spec in definitions:
        key = str(spec["segment_key"])
        row = session.scalar(select(MarketSegment).where(MarketSegment.game_year == game_year, MarketSegment.segment_key == key))
        if row is None:
            row = MarketSegment(game_year=game_year, provider_support_json={}, metadata_json={}, **spec)
            session.add(row)
            session.flush()
        rows[key] = row
    return rows


def get_market_segment(session: Session, *, game_year: int, segment_key: str) -> MarketSegment:
    rows = ensure_market_segments(session, game_year=game_year)
    normalized = segment_key.upper()
    if normalized not in rows:
        normalized = MarketSegmentKey.UNKNOWN.value
    return rows[normalized]


def ensure_account_market_access(session: Session, account: TradingAccount, *, game_year: int = 26) -> None:
    rows = ensure_market_segments(session, game_year=game_year)
    now = datetime.now(UTC)
    for key, segment in rows.items():
        access = session.scalar(select(AccountMarketAccess).where(
            AccountMarketAccess.account_id == account.id,
            AccountMarketAccess.market_segment_id == segment.id,
        ))
        executable = key == MarketSegmentKey.PC.value and game_year == 26
        if access is None:
            session.add(AccountMarketAccess(
                account_id=account.id,
                market_segment_id=segment.id,
                executable=executable,
                enabled=True,
                updated_at=now,
                metadata_json={},
            ))
        else:
            access.executable = executable
            access.updated_at = now
    session.flush()


def is_executable_segment(session: Session, *, account_id, market_segment_id) -> bool:
    row = session.scalar(select(AccountMarketAccess).where(
        AccountMarketAccess.account_id == account_id,
        AccountMarketAccess.market_segment_id == market_segment_id,
        AccountMarketAccess.enabled.is_(True),
    ))
    return bool(row and row.executable)
