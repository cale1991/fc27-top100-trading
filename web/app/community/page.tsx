"use client";
import { useEffect, useState } from "react";
import { api, coins, pct } from "@/lib/api";
import { ErrorBox, Loading } from "@/components/Loading";

export default function CommunityPage(){
 const [data,setData]=useState<any>(null);const [error,setError]=useState("");useEffect(()=>{api<any>("/community").then(setData).catch(e=>setError(e.message))},[]);
 return <><header className="pageHead"><div><h1>Community / traders</h1><p>Calls are weighted by measured predictive performance, not follower count.</p></div></header>{error&&<ErrorBox error={error}/>} {!data?<Loading/>:<div className="grid2"><section className="panel"><div className="panelTitle"><h2>Important tracked calls</h2></div>{data.important_calls?.length?data.important_calls.map((x:any)=><div className="activityItem" key={x.id}><div></div><div><strong>{x.direction.toUpperCase()} · {coins(x.entry)} → {coins(x.target)}</strong><p>{x.category||"Card call"} · {x.catalyst||"No catalyst extracted"}</p></div></div>):<p className="muted">No permitted community source has been configured/ingested yet.</p>}</section><section className="panel"><div className="panelTitle"><h2>Trader accuracy</h2></div>{data.trader_leaderboard?.length?<div className="tableWrap"><table className="dataTable"><thead><tr><th>Trader</th><th>Score</th><th>Calls</th><th>Directional</th><th>After tax</th></tr></thead><tbody>{data.trader_leaderboard.map((x:any)=><tr key={x.trader_id}><td>{x.handle}</td><td>{pct(x.reputation_score)}</td><td>{x.sample_size}</td><td>{pct(x.directional_accuracy)}</td><td>{pct(x.profitable_after_tax_rate)}</td></tr>)}</tbody></table></div>:<p className="muted">Reputation scores appear after tracked calls have outcomes.</p>}</section></div>}</>;
}
