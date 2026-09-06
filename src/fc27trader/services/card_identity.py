from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fc27trader.db.models import Card, CardSourceId, Source


def resolve_card_for_provider(
    session: Session,
    *,
    source: Source,
    external_id: str,
    game_year: int,
    ea_resource_id: int | None,
    name: str,
    rating: int | None,
    primary_position: str | None,
    league: str | None,
    club: str | None,
    nation: str | None,
) -> tuple[Card | None, str, float]:
    mapping = session.scalar(
        select(CardSourceId).where(CardSourceId.source_id == source.id, CardSourceId.external_id == external_id)
    )
    if mapping:
        return session.get(Card, mapping.card_id), "existing_source_id", float(mapping.mapping_confidence or 1.0)

    if ea_resource_id is not None:
        card = session.scalar(
            select(Card).where(Card.game_year == game_year, Card.ea_resource_id == ea_resource_id)
        )
        if card:
            return card, "ea_resource_id", 1.0

    # Conservative cross-provider fallback. Only accept one exact match; ambiguity
    # creates a separate card rather than silently merging different versions.
    clauses = [Card.game_year == game_year, func.lower(Card.name) == name.lower()]
    if rating is not None:
        clauses.append(Card.rating == rating)
    # Position is optional provider metadata, not part of canonical card identity.
    # Live providers can emit decorated/composite/malformed position strings. Stable
    # provider IDs, EA resource IDs, player/version/rating and club/league/nation are
    # stronger identity evidence and must not be invalidated by position metadata.
    if league:
        clauses.append(Card.league == league)
    if club:
        clauses.append(Card.club == club)
    if nation:
        clauses.append(Card.nation == nation)
    matches = list(session.scalars(select(Card).where(*clauses).limit(2)))
    if len(matches) == 1:
        return matches[0], "exact_identity_fingerprint", 0.88
    return None, "new_provider_card", 1.0


def ensure_source_mapping(
    session: Session,
    *,
    card: Card,
    source: Source,
    external_id: str,
    source_url: str | None,
    mapping_method: str,
    mapping_confidence: float,
) -> CardSourceId:
    row = session.scalar(select(CardSourceId).where(CardSourceId.source_id == source.id, CardSourceId.external_id == external_id))
    if row:
        return row
    if mapping_method in {"existing_source_id", "ea_resource_id"}:
        mapping_status = "CONFIRMED"
    elif mapping_confidence >= 0.95:
        mapping_status = "HIGH_CONFIDENCE"
    elif mapping_confidence >= 0.80:
        mapping_status = "PROBABLE"
    else:
        mapping_status = "UNRESOLVED"
    row = CardSourceId(
        card_id=card.id,
        source_id=source.id,
        external_id=external_id,
        source_url=source_url,
        mapping_method=mapping_method,
        mapping_confidence=Decimal(str(mapping_confidence)),
        mapping_status=mapping_status,
    )
    session.add(row)
    session.flush()
    return row
