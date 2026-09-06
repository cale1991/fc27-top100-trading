"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Opportunity } from "@/lib/types";
import { useLiveRefresh } from "@/lib/live";
import { OpportunityRow } from "@/components/OpportunityRow";
import { ErrorBox, Loading } from "@/components/Loading";

export default function OpportunitiesPage(){
 const [rows,setRows]=useState<Opportunity[]|null>(null); const [error,setError]=useState("");
 const load=useCallback(async()=>{try{setRows(await api<Opportunity[]>("/opportunities?limit=100"));setError("")}catch(e){setError((e as Error).message)}},[]);
 useEffect(()=>{load()},[load]);useLiveRefresh(load);
 return <><header className="pageHead"><div><h1>Opportunities</h1><p>Dynamic candidates across observed markets. Actionable PC opportunities rank first; non-PC evidence remains research context and can trigger PC verification.</p></div></header>{error&&<ErrorBox error={error}/>} {!rows?<Loading/>:<section className="panel">{rows.length?rows.map(x=><OpportunityRow key={x.id} x={x}/>):<p className="muted">No current candidates passed the opportunity threshold.</p>}</section>}</>;
}
