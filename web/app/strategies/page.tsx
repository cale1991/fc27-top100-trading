"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, coins, pct } from "@/lib/api";
import { ErrorBox, Loading } from "@/components/Loading";

export default function StrategiesPage(){
 const [rows,setRows]=useState<any[]|null>(null); const [active,setActive]=useState<any[]>([]); const [discoveries,setDiscoveries]=useState<any[]>([]); const [error,setError]=useState("");
 useEffect(()=>{Promise.all([api<any[]>("/strategies"),api<any[]>("/strategies/active"),api<any[]>("/strategies/discoveries")]).then(([a,b,c])=>{setRows(a);setActive(b);setDiscoveries(c)}).catch(e=>setError((e as Error).message))},[]);
 if(error&&!rows)return <ErrorBox error={error}/>; if(!rows)return <Loading/>;
 return <><header className="pageHead"><div><h1>Strategies / Research</h1><p>Historical mechanisms are evidence, not a fixed production playbook.</p></div></header>
 <section className="panel"><div className="panelTitle"><h2>Active historical patterns</h2><span className="muted">{active.length} live matches</span></div>{active.length?active.slice(0,12).map((x:any,i:number)=><Link href={`/opportunities/${x.candidate_id}`} className="activityItem" key={`${x.candidate_id}-${x.strategy_slug}-${i}`}><div></div><div><strong>{x.card} · {x.strategy_name}</strong><p>similarity {pct(x.similarity)} · confidence {pct(x.confidence)} · measured n={x.historical_sample_size||0}{x.current_conditions_differ?" · current conditions differ":""}</p></div></Link>):<p className="muted">No current opportunity has a stored historical-strategy match yet.</p>}</section>
 <section className="panel" style={{marginTop:12}}><div className="panelTitle"><h2>Strategy library</h2><span className="muted">measured performance stays blank until FC26 samples exist</span></div><div className="tableWrap"><table className="dataTable"><thead><tr><th>Strategy</th><th>Evidence</th><th>Status</th><th>FC26 n</th><th>Hit rate</th><th>Net TP</th><th>Active</th></tr></thead><tbody>{rows.map((x:any)=><tr key={x.slug}><td><Link className="linkButton" href={`/strategies/${x.slug}`}>{x.name}</Link></td><td>{x.evidence_class}</td><td>{x.viability_status}</td><td>{x.sample_size||0}</td><td>{pct(x.hit_rate)}</td><td>{coins(x.total_net_transfer_profit)}</td><td>{x.active_matches||0}</td></tr>)}</tbody></table></div></section>
 <section className="panel" style={{marginTop:12}}><div className="panelTitle"><h2>Emerging unnamed patterns</h2></div>{discoveries.length?discoveries.map((x:any)=><div className="activityItem" key={x.pattern_key}><div></div><div><strong>{x.pattern_key} · {x.status}</strong><p>n={x.sample_size} · confidence {pct(x.confidence)} · {x.description||"quantitative pattern under observation"}</p></div></div>):<p className="muted">No quantitative pattern has reached the discovery registry yet.</p>}</section></>;
}
