from datetime import UTC, datetime
from fc27trader.strategy.matching import match_strategy, recognize_strategies
from fc27trader.strategy.models import StrategyContext, StrategyDefinition


def ctx(**kw):
    base=dict(card_id='x', observed_at=datetime.now(UTC), card_category='fodder', market_regime='normal', catalysts=('sbc',), in_packs=False, liquidity_score=0.8, demand_score=0.7)
    base.update(kw); return StrategyContext(**base)


def test_out_of_pack_rule_matches():
    d=StrategyDefinition(slug='oop',name='OOP',card_categories=('fodder',),rule={'requires_out_of_packs':True})
    m=match_strategy(d,ctx())
    assert m is not None and m.similarity >= .9


def test_category_mismatch_can_be_rejected():
    d=StrategyDefinition(slug='icon',name='Icon',card_categories=('icon',),market_regimes=('panic',),rule={'min_liquidity':.95})
    assert match_strategy(d,ctx()) is None
