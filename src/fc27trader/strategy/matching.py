from __future__ import annotations

from .models import StrategyContext, StrategyDefinition, StrategyMatch


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _terms(values) -> set[str]:
    return {str(x).strip().lower() for x in (values or []) if str(x).strip()}


def _rule_fit(rule: dict, ctx: StrategyContext) -> tuple[float, list[str], bool]:
    if not rule:
        return 0.5, [], False
    checks: list[bool] = []
    reasons: list[str] = []
    differs = False
    for key, value in rule.items():
        ok = True
        if key == "requires_out_of_packs":
            ok = ctx.in_packs is False if value else True
            if ok: reasons.append("card is out of packs")
        elif key == "requires_in_packs":
            ok = ctx.in_packs is True if value else True
            if ok: reasons.append("card remains in packs")
        elif key == "min_liquidity":
            ok = ctx.liquidity_score is not None and ctx.liquidity_score >= float(value)
            if ok: reasons.append("liquidity fits historical setup")
        elif key == "min_demand_score":
            ok = ctx.demand_score is not None and ctx.demand_score >= float(value)
            if ok: reasons.append("demand fits historical setup")
        elif key == "max_price_change_1h":
            ok = ctx.price_change_1h is not None and ctx.price_change_1h <= float(value)
            if ok: reasons.append("1h move resembles historical entry condition")
        elif key == "max_price_change_24h":
            ok = ctx.price_change_24h is not None and ctx.price_change_24h <= float(value)
            if ok: reasons.append("24h move resembles historical entry condition")
        elif key == "max_seconds_to_content":
            ok = ctx.seconds_to_content is not None and ctx.seconds_to_content <= float(value)
            if ok: reasons.append("content timing fits historical setup")
        elif key == "max_seconds_since_content":
            ok = ctx.seconds_since_content is not None and ctx.seconds_since_content <= float(value)
            if ok: reasons.append("recent content timing fits historical setup")
        # Unknown rules are not treated as failures; they remain available for richer models.
        else:
            continue
        checks.append(bool(ok))
        differs = differs or not ok
    return (sum(checks) / len(checks) if checks else 0.5), reasons, differs


def match_strategy(definition: StrategyDefinition, ctx: StrategyContext) -> StrategyMatch | None:
    score_parts: list[float] = []
    reasons: list[str] = []
    differs = False

    categories = _terms(definition.card_categories)
    if categories and ctx.card_category:
        hit = ctx.card_category.lower() in categories
        score_parts.append(1.0 if hit else 0.0)
        if hit: reasons.append(f"card category: {ctx.card_category}")
        else: differs = True

    regimes = _terms(definition.market_regimes)
    if regimes and ctx.market_regime:
        hit = ctx.market_regime.lower() in regimes
        score_parts.append(1.0 if hit else 0.15)
        if hit: reasons.append(f"market regime: {ctx.market_regime}")
        else: differs = True

    wanted_catalysts = _terms(definition.catalysts)
    current_catalysts = _terms(ctx.catalysts)
    if wanted_catalysts and current_catalysts:
        overlap = wanted_catalysts & current_catalysts
        score_parts.append(min(1.0, len(overlap) / max(1, min(2, len(wanted_catalysts)))))
        if overlap: reasons.append("catalyst: " + ", ".join(sorted(overlap)[:3]))

    rule_score, rule_reasons, rule_differs = _rule_fit(definition.rule, ctx)
    score_parts.append(rule_score)
    reasons.extend(rule_reasons)
    differs = differs or rule_differs

    if not score_parts:
        return None
    similarity = _clamp(sum(score_parts) / len(score_parts))
    # Avoid noisy strategy labels. Current evidence can still rank the card with no named match.
    if similarity < 0.42:
        return None
    confidence = _clamp(0.25 + similarity * 0.55 + min(len(reasons), 4) * 0.04)
    return StrategyMatch(
        slug=definition.slug,
        name=definition.name,
        similarity=similarity,
        confidence=confidence,
        reasons=tuple(reasons),
        current_conditions_differ=differs,
    )


def recognize_strategies(
    ctx: StrategyContext,
    definitions: list[StrategyDefinition],
    *,
    max_matches: int = 5,
) -> list[StrategyMatch]:
    matches = [m for d in definitions if (m := match_strategy(d, ctx)) is not None]
    matches.sort(key=lambda m: (m.similarity * m.confidence), reverse=True)
    return matches[:max_matches]
