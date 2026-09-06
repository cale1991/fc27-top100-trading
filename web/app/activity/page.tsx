"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useLiveRefresh } from "@/lib/live";
import { ErrorBox, Loading } from "@/components/Loading";

export default function ActivityPage(){
 const [rows,setRows]=useState<any[]|null>(null);const [error,setError]=useState("");
 const load=useCallback(async()=>{try{setRows(await api<any[]>("/activity?limit=200"));setError("")}catch(e){setError((e as Error).message)}},[]);useEffect(()=>{load()},[load]);useLiveRefresh(load);
 return <><header className="pageHead"><div><h1>Activity</h1><p>Human-readable market, content, verification and portfolio timeline.</p></div></header>{error&&<ErrorBox error={error}/>} {!rows?<Loading/>:<section className="panel">{rows.length?rows.map(x=><div className="activityItem" key={x.id}><time>{x.at?new Date(x.at).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}):"—"}</time><div><strong>{x.title}</strong><p>{x.message||`${x.category}${x.event_type?` · ${x.event_type}`:""}`}</p></div></div>):<p className="muted">No activity recorded yet.</p>}</section>}</>;
}
