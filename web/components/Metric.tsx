import { ReactNode } from "react";
export function Metric({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong>{sub ? <small>{sub}</small> : null}</div>;
}
