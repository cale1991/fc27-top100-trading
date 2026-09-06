"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useEffect } from "react";

const nav = [
  ["/", "Now"],
  ["/opportunities", "Opportunities"],
  ["/verify", "Verify"],
  ["/portfolio", "Portfolio"],
  ["/market", "Market"],
  ["/activity", "Activity"],
  ["/community", "Community"],
  ["/strategies", "Strategies"],
  ["/system", "System"],
];

export function AppShell({ children }: { children: ReactNode }) {
  const path = usePathname();
  useEffect(() => {
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  }, []);
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brandMark">FC</span><div><strong>Trading Terminal</strong><small>PC market · FC26 rehearsal</small></div></div>
        <nav>{nav.map(([href, label]) => <Link key={href} href={href} className={path === href || (href !== "/" && path.startsWith(href)) ? "active" : ""}>{label}</Link>)}</nav>
      </aside>
      <main className="main">{children}</main>
      <nav className="mobileNav">{[["/","Now"],["/opportunities","Opportunities"],["/verify","Verify"],["/portfolio","Portfolio"],["/more","More"]].map(([href,label]) => <Link key={href} href={href} className={path === href || (href !== "/" && path.startsWith(href)) ? "active" : ""}>{label}</Link>)}</nav>
    </div>
  );
}
