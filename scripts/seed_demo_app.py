"""Optional local UI demo data. Never run against the production database."""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from fc27trader.db.models import Card, ManualVerificationRequest, OpportunityCandidate
from fc27trader.db.repositories import insert_reference_price_observation, upsert_external_card
from fc27trader.db.session import SessionLocal
from fc27trader.services.portfolio import get_or_create_account, set_coin_balance
from fc27trader.settings import get_settings

settings = get_settings()
if settings.app_env.lower() in {"prod", "production"}:
    raise SystemExit("Refusing to seed demo data in production")

with SessionLocal() as session:
    account = get_or_create_account(session)
    if account.current_coins == 0:
        set_coin_balance(session, account, 500_000, notes="local demo seed")
    card = upsert_external_card(
        session,
        source_key="demo_local",
        external_id="demo-001",
        game_year=26,
        name="DEMO Market Candidate",
        rating=88,
        primary_position="ST",
        league="Demo League",
        club="Demo FC",
        nation="Demo",
        rarity="Promo Test",
        attributes={},
    )
    now = datetime.now(UTC)
    ref = insert_reference_price_observation(
        session,
        card=card,
        source_key="demo_local",
        observed_at=now,
        provider_timestamp=now - timedelta(minutes=8),
        price=101_000,
        historical_provider_error_pct=0.025,
        uncertainty_pct=0.08,
        confidence=0.72,
        metadata={"demo": True},
    )
    candidate = OpportunityCandidate(
        card_id=card.id,
        platform="pc",
        discovered_at=now,
        last_scored_at=now,
        expires_at=now + timedelta(hours=1),
        status="needs_verification",
        rank=1,
        opportunity_score=Decimal("2.85"),
        reference_observation_id=ref.id,
        expected_acquisition_price=95_500,
        acquisition_probability=Decimal("0.61"),
        expected_discount_to_reference=Decimal("0.054455"),
        profitable_exit_probability=Decimal("0.78"),
        expected_net_profit=8_200,
        expected_profit_per_hour=Decimal("4100"),
        expected_holding_seconds=7200,
        position_capacity_coins=480_000,
        liquidity_score=Decimal("0.82"),
        sell_through_rate=Decimal("0.74"),
        volatility=Decimal("0.06"),
        downside_risk=Decimal("0.08"),
        catalyst_score=Decimal("0.73"),
        ea_intervention_risk=Decimal("0.24"),
        opportunity_cost=Decimal("1200"),
        requires_manual_verification=True,
        action="buy",
        max_recommended_buy_price=96_000,
        target_sell_low=103_000,
        target_sell_high=105_000,
        recommended_quantity=3,
        expected_roi=Decimal("0.02847"),
        confidence_score=Decimal("0.72"),
        main_catalyst="Demo: reference/execution verification workflow",
        invalidation_condition="Current lowest PC BIN moves above 99k with no undercuts",
        exit_logic="List into the 103k-105k region if current sell-through remains healthy",
        score_components_json={"expected_net_profit": 0.8, "liquidity_score": 0.7},
        metadata_json={"demo": True},
    )
    session.add(candidate)
    session.flush()
    existing = session.scalar(select(ManualVerificationRequest).where(ManualVerificationRequest.candidate_id == candidate.id))
    if not existing:
        session.add(
            ManualVerificationRequest(
                candidate_id=candidate.id,
                card_id=card.id,
                platform="pc",
                requested_at=now,
                priority=8,
                status="pending",
                reason="Demo BUY candidate lacks fresh execution data",
                reference_observation_id=ref.id,
                latest_reference_price=101_000,
                reference_timestamp=now - timedelta(minutes=8),
                reference_uncertainty_pct=Decimal("0.08"),
                expected_acquisition_min=94_500,
                expected_acquisition_max=96_000,
                attractive_at_or_below=96_000,
                required_information="current lowest 5-10 PC BIN listings for exact card/version",
                expected_information_value=Decimal("4200"),
                expires_at=now + timedelta(hours=1),
                metadata_json={"demo": True},
            )
        )
    session.commit()
    print("Demo state seeded. Open http://localhost:3000 and use prices <= 96000 to exercise BUY verification.")
