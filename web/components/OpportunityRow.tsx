import Link from "next/link";
import { Opportunity } from "@/lib/types";
import { age, coins, duration, pct } from "@/lib/api";
import { ActionBadge } from "./ActionBadge";

export function OpportunityRow({ x }: { x: Opportunity }) {
  return <Link href={`/opportunities/${x.id}`} className="opportunityRow">
    <div className="oppIdentity"><strong>{x.rating ? `${x.rating} ` : ""}{x.card}</strong><span>{x.card_version} · {(x as any).market_segment || "PC"}{(x as any).actionable===false?" · RESEARCH":""}</span></div>
    <ActionBadge action={x.action} />
    <div><small>Reference</small><strong>{coins(x.reference_price)}</strong><span>{x.reference_source||"reference"} · {age(x.reference_age_seconds)} old</span></div>
    <div><small>Buy ≤</small><strong>{coins(x.max_buy_price)}</strong><span>{x.recommended_quantity || 1}x</span></div>
    <div><small>Net profit</small><strong className={(x.expected_net_profit || 0) >= 0 ? "positive" : "negative"}>{coins(x.expected_net_profit)}</strong><span>{pct(x.expected_roi)}</span></div>
    <div><small>Profit / h</small><strong>{coins(x.expected_profit_per_hour)}</strong><span>{duration(x.expected_holding_seconds)}</span></div>
    <div><small>Trade/model confidence</small><strong>{pct(x.trade_model_confidence ?? x.confidence)}</strong><span>liq {pct(x.liquidity_score)}</span></div>
  </Link>;
}
