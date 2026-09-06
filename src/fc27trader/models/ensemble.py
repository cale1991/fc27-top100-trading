from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelSignal:
    model_key: str
    predicted_net_profit: float
    profitable_exit_probability: float
    confidence: float
    independent_value_weight: float = 1.0


@dataclass(frozen=True, slots=True)
class EnsembleEstimate:
    predicted_net_profit: float | None
    profitable_exit_probability: float | None
    agreement: float
    models_used: int


def combine_signals(signals: list[ModelSignal]) -> EnsembleEstimate:
    valid=[s for s in signals if s.confidence>0 and s.independent_value_weight>0]
    if not valid:return EnsembleEstimate(None,None,0.0,0)
    weights=[s.confidence*s.independent_value_weight for s in valid]; total=sum(weights)
    profit=sum(s.predicted_net_profit*w for s,w in zip(valid,weights))/total
    prob=sum(s.profitable_exit_probability*w for s,w in zip(valid,weights))/total
    signs=[1 if s.predicted_net_profit>0 else -1 if s.predicted_net_profit<0 else 0 for s in valid]
    majority=max(signs.count(1),signs.count(-1),signs.count(0))/len(signs)
    return EnsembleEstimate(profit,prob,majority,len(valid))
