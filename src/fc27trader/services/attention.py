from __future__ import annotations

from dataclasses import dataclass

from fc27trader.opportunity.models import OpportunityInputs, RankedOpportunity


@dataclass(frozen=True, slots=True)
class AttentionDecision:
    card_id: str
    attention_score: float
    tier: str
    target_interval_seconds: int
    reasons: list[str]


def allocate_attention(
    opportunities: list[RankedOpportunity],
    inputs_by_card: dict[str, OpportunityInputs],
) -> list[AttentionDecision]:
    """Recompute observation effort from current state, not a permanent watchlist."""
    decisions: list[AttentionDecision] = []
    for candidate in opportunities:
        item = inputs_by_card[candidate.card_id]
        score = candidate.score
        reasons = ["ranked_opportunity"]
        if item.active_position:
            score += 1.25
            reasons.append("active_position")
        if (item.catalyst_score or 0) >= 0.7:
            score += 0.65
            reasons.append("strong_catalyst")
        if (item.rapid_movement_score or 0) >= 0.7:
            score += 0.60
            reasons.append("rapid_movement")
        if (item.unusual_volume_score or 0) >= 0.7:
            score += 0.45
            reasons.append("unusual_volume")

        if score >= 2.5:
            tier, interval = "critical", 120
        elif score >= 1.5:
            tier, interval = "hot", 120
        elif score >= 0.75:
            tier, interval = "active", 300
        else:
            tier, interval = "background", 900
        decisions.append(AttentionDecision(candidate.card_id, score, tier, interval, reasons))
    return decisions
