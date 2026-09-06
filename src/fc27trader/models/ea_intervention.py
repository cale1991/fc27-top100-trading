from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EAInterventionInputs:
    store_pack_supply_score: float = 0.0
    pack_probability_increase_score: float = 0.0
    rewards_supply_score: float = 0.0
    sbc_demand_score: float = 0.0
    evo_demand_score: float = 0.0
    substitute_release_score: float = 0.0
    price_range_change_score: float = 0.0
    leaving_packs: bool = False


@dataclass(frozen=True, slots=True)
class EAInterventionEstimate:
    downside_risk: float
    demand_support: float
    net_risk: float
    reasons: list[str]


def estimate_ea_intervention_risk(x: EAInterventionInputs) -> EAInterventionEstimate:
    supply = 0.30*x.store_pack_supply_score + 0.20*x.pack_probability_increase_score + 0.20*x.rewards_supply_score + 0.20*x.substitute_release_score + 0.10*x.price_range_change_score
    demand = 0.60*x.sbc_demand_score + 0.40*x.evo_demand_score
    reasons=[]
    if x.store_pack_supply_score>0.5: reasons.append("store_pack_supply")
    if x.substitute_release_score>0.5: reasons.append("new_substitute")
    if x.sbc_demand_score>0.5: reasons.append("sbc_demand_support")
    if x.evo_demand_score>0.5: reasons.append("evo_demand_support")
    if x.leaving_packs:
        demand=min(1.0,demand+0.15); reasons.append("leaving_packs_supply_support")
    net=max(0.0,min(1.0,supply-0.35*demand))
    return EAInterventionEstimate(max(0.0,min(1.0,supply)),max(0.0,min(1.0,demand)),net,reasons)
