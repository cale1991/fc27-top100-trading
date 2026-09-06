"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, coins, pct } from "@/lib/api";
import { Opportunity } from "@/lib/types";
import { useLiveRefresh } from "@/lib/live";
import { Metric } from "@/components/Metric";
import { OpportunityRow } from "@/components/OpportunityRow";
import { ErrorBox, Loading } from "@/components/Loading";

export default function Dashboard() {
  const [data,setData]=useState<any>(null); const [activity,setActivity]=useState<any[]>([]); const [error,setError]=useState("");
  const load=useCallback(async()=>{try{const [d,a]=await Promise.all([api<any>("/dashboard"),api<any[]>("/activity?limit=8")]);setData(d);setActivity(a);setError("");}catch(e){setError((e as Error).message)}},[]);
  useEffect(()=>{load()},[load]); useLiveRefresh(load);
  if(error&&!data)return <ErrorBox error={error}/>; if(!data)return <Loading/>;
  return <>
    <header className="pageHead"><div><h1>What should I do right now?</h1><p>Only the strongest current PC-market actions.</p></div><span className="timestamp">Updated {new Date(data.generated_at).toLocaleTimeString()}</span></header>
    <section className="metrics">
      <Metric label="Available coins" value={coins(data.available_capital)}/><Metric label="Deployed" value={coins(data.deployed_coins)}/>
      <Metric label="Transfer Profit today" value={<span className={data.transfer_profit_today>=0?"positive":"negative"}>{coins(data.transfer_profit_today)}</span>} sub={`Week ${coins(data.transfer_profit_week)}`}/>
      <Metric label="Total Transfer Profit" value={coins(data.total_transfer_profit)} sub={`Unrealized ${coins(data.unrealized_expected_profit)}`}/>
      <Metric label="Active positions" value={data.active_positions}/><Metric label="Needs verification" value={data.verification_requests} sub={data.verification_requests?<Link href="/verify">Open requests</Link>:"Clear"}/>
      <Metric label="Market regime" value={data.market_regime}/><Metric label="EA intervention risk" value={pct(data.ea_intervention_risk)} sub="Highest active candidate"/>
      <Metric label="Leaderboard target" value={data.leaderboard?.data_available ? `#${data.leaderboard.rank ?? "—"}` : (data.leaderboard?.target ?? "Top 100")} sub={data.leaderboard?.data_available ? "Current tracked rank" : "Rank feed not available yet"}/>
    </section>
    <div className="grid2">
      <section className="panel"><div className="panelTitle"><h2>Best opportunities</h2><Link href="/opportunities">All opportunities →</Link></div>{data.top_opportunities?.length?data.top_opportunities.map((x:Opportunity)=><OpportunityRow key={x.id} x={x}/>):<p className="muted">No ranked candidates yet. Collection can keep running while the app is empty.</p>}</section>
      <div className="stack">
        {data.verification_requests>0&&<section className="panel verifyCard"><div className="panelTitle"><h2>Verification needed</h2><Link href="/verify">Verify now →</Link></div><p className="muted">{data.verification_requests} candidate{data.verification_requests===1?"":"s"} need current PC listings before acting.</p></section>}
        {data.urgent_positions?.length>0&&<section className="panel"><div className="panelTitle"><h2>Urgent portfolio actions</h2></div>{data.urgent_positions.map((p:any)=><div key={p.position_id} className="activityItem"><strong>{p.card}</strong><p>{String(p.current_action).toUpperCase()} · urgency {p.urgency}/10</p></div>)}</section>}
        <section className="panel"><div className="panelTitle"><h2>Activity</h2><Link href="/activity">Timeline →</Link></div>{activity.slice(0,7).map((x:any)=><div className="activityItem" key={x.id}><time>{x.at?new Date(x.at).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}):"—"}</time><div><strong>{x.title}</strong>{x.message&&<p>{x.message}</p>}</div></div>)}</section>
      </div>
    </div>
  </>;
}
