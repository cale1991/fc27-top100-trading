export function ActionBadge({ action }: { action?: string | null }) {
  const value = (action || "WATCH").replaceAll("_", " ").toUpperCase();
  const cls = value.toLowerCase().replaceAll(" ", "-");
  return <span className={`action action-${cls}`}>{value}</span>;
}
