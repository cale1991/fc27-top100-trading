export function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return <div className="emptySpark">No price history yet</div>;
  const w=700, h=180, pad=8, min=Math.min(...values), max=Math.max(...values), range=Math.max(1,max-min);
  const points=values.map((v,i)=>`${pad + i*(w-pad*2)/(values.length-1)},${h-pad-(v-min)*(h-pad*2)/range}`).join(" ");
  return <svg className="spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none"><polyline points={points} fill="none" stroke="currentColor" strokeWidth="3" vectorEffect="non-scaling-stroke"/></svg>;
}
