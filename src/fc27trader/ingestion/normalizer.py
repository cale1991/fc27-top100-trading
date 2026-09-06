from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import orjson

from fc27trader.collectors.base import RawObservation
from fc27trader.domain.enums import Platform
from fc27trader.domain.market import MarketSnapshot


@dataclass(slots=True)
class NormalizedCardRecord:
    source_key: str
    external_id: str
    game_year: int
    name: str
    rating: int | None
    primary_position: str | None
    alt_positions: list[str]
    league: str | None
    club: str | None
    nation: str | None
    rarity: str | None
    attributes: dict[str, Any]
    source_updated_at: datetime | str | None
    ea_resource_id: int | None = None
    ea_asset_id: int | None = None
    playstyles: list[str] | None = None
    playstyles_plus: list[str] | None = None
    roles: dict[str, Any] | None = None
    image_id: str | None = None
    image_url: str | None = None
    source_url: str | None = None
    cross_provider_ids: dict[str, str] | None = None


def normalize_thecoinprinter(obs: RawObservation) -> tuple[list[NormalizedCardRecord], list[MarketSnapshot]]:
    payload = orjson.loads(obs.body)
    cards: list[NormalizedCardRecord] = []
    snapshots: list[MarketSnapshot] = []
    for player in payload.get("data", []):
        player_id = str(player["id"])
        source_updated_at = player.get("updated_at")
        attributes = {
            k: player.get(k)
            for k in ("pace", "shooting", "passing", "dribbling", "defending", "physical", "popularity")
            if player.get(k) is not None
        }
        cards.append(
            NormalizedCardRecord(
                source_key="thecoinprinter",
                external_id=player_id,
                game_year=int(player.get("year") or 26),
                name=player.get("name") or f"unknown:{player_id}",
                rating=player.get("rating"),
                primary_position=player.get("position"),
                alt_positions=player.get("alt_positions") or [],
                league=player.get("league"),
                club=player.get("team"),
                nation=player.get("nationality"),
                rarity=player.get("group_type"),
                attributes=attributes,
                source_updated_at=source_updated_at,
                image_id=player_id,
                image_url=player.get("image"),
                source_url="https://www.thecoinprinter.com/",
            )
        )
        for platform, field in ((Platform.PC, "pc_price"), (Platform.CONSOLE, "console_price")):
            snapshots.append(
                MarketSnapshot(
                    card_external_id=player_id,
                    source_key="thecoinprinter",
                    platform=platform,
                    source_timestamp=source_updated_at,
                    observed_at=obs.observed_at,
                    lowest_bin=player.get(field),
                    source_updated_at=source_updated_at,
                )
            )
    return cards, snapshots



def normalize_futdb_players(
    obs: RawObservation,
    *,
    entity_names: dict[str, dict[str, str]] | None = None,
) -> tuple[list[NormalizedCardRecord], dict[str, Any]]:
    """Normalize FUT-DB's documented PlayersResponse for FC26.

    FUT-DB uses numeric IDs for league/club/nation/rarity. entity_names is populated
    from its documented metadata endpoints when available; numeric IDs are always
    retained in attributes so later enrichment never loses source identity.
    """
    payload = orjson.loads(obs.body)
    names = entity_names or {}
    cards: list[NormalizedCardRecord] = []
    for player in payload.get("items") or []:
        pid = str(player["id"])
        league_id = player.get("league")
        club_id = player.get("club")
        nation_id = player.get("nation")
        rarity_id = player.get("rarity")
        attrs = {
            "resource_base_id": player.get("resourceBaseId"),
            "gender": player.get("gender"),
            "height": player.get("height"),
            "weight": player.get("weight"),
            "weak_foot": player.get("weakFoot"),
            "skill_moves": player.get("skillMoves"),
            "preferred_foot": player.get("foot"),
            "attack_work_rate": player.get("attackWorkRate"),
            "defense_work_rate": player.get("defenseWorkRate"),
            "total_stats": player.get("totalStats"),
            "total_stats_ingame": player.get("totalStatsInGame"),
            "color": player.get("color"),
            "league_id": league_id,
            "club_id": club_id,
            "nation_id": nation_id,
            "rarity_id": rarity_id,
            "rarity_groups": player.get("rarity_groups") or [],
            "pace": player.get("pace"),
            "shooting": player.get("shooting"),
            "passing": player.get("passing"),
            "dribbling": player.get("dribbling"),
            "defending": player.get("defending"),
            "physicality": player.get("physicality"),
            "pace_attributes": player.get("paceAttributes"),
            "shooting_attributes": player.get("shootingAttributes"),
            "passing_attributes": player.get("passingAttributes"),
            "dribbling_attributes": player.get("dribblingAttributes"),
            "defending_attributes": player.get("defendingAttributes"),
            "physicality_attributes": player.get("physicalityAttributes"),
            "goalkeeper_attributes": player.get("goalkeeperAttributes"),
        }
        attrs = {k: v for k, v in attrs.items() if v is not None}
        playstyles = player.get("playStyles") or []
        plus = player.get("playStylesPlus") or []
        cards.append(
            NormalizedCardRecord(
                source_key="futdb",
                external_id=pid,
                game_year=26,
                name=player.get("commonName") or player.get("name") or f"unknown:{pid}",
                rating=player.get("rating"),
                primary_position=player.get("position"),
                alt_positions=player.get("positionAlternatives") or [],
                league=names.get("league", {}).get(str(league_id)) if league_id is not None else None,
                club=names.get("club", {}).get(str(club_id)) if club_id is not None else None,
                nation=names.get("nation", {}).get(str(nation_id)) if nation_id is not None else None,
                rarity=names.get("rarity", {}).get(str(rarity_id)) if rarity_id is not None else None,
                attributes=attrs,
                source_updated_at=None,
                ea_resource_id=player.get("resourceId"),
                playstyles=playstyles,
                playstyles_plus=plus,
                roles={},
                image_id=pid,
                image_url=f"https://api.fut-db.com/api/players/{pid}/image",
                source_url=f"https://api.fut-db.com/api/players/{pid}",
                cross_provider_ids={
                    k: str(v)
                    for k, v in {
                        "futbin": player.get("futBinId"),
                        "futwiz": player.get("futWizId"),
                    }.items()
                    if v is not None
                },
            )
        )
    return cards, payload.get("pagination") or {}


def normalize_futdb_price(obs: RawObservation, *, player_id: int | str) -> MarketSnapshot | None:
    payload = orjson.loads(obs.body)
    pc = payload.get("pc") or {}
    price = pc.get("price")
    if price is None:
        return None
    return MarketSnapshot(
        card_external_id=str(player_id),
        source_key="futdb",
        platform=Platform.PC,
        source_timestamp=pc.get("priceUpdate"),
        observed_at=obs.observed_at,
        lowest_bin=price,
        source_updated_at=pc.get("priceUpdate"),
    )


def normalize_futdb_entities(obs: RawObservation, entity_type: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = orjson.loads(obs.body)
    rows = []
    for item in payload.get("items") or []:
        rows.append({
            "entity_type": entity_type,
            "external_id": str(item["id"]),
            "name": item.get("name"),
            "metadata": item,
        })
    return rows, payload.get("pagination") or {}
