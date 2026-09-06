export function Loading({ text="Loading market state…" }: {text?: string}) { return <div className="panel mutedPanel">{text}</div>; }
export function ErrorBox({ error }: {error: string}) { return <div className="panel errorPanel">{error}</div>; }
