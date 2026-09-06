import Link from "next/link";
const links=[["/market","Market research"],["/activity","Activity"],["/community","Community"],["/strategies","Strategies / Research"],["/system","Models / System"]];
export default function More(){return <><header className="pageHead"><div><h1>More</h1><p>Research and system views.</p></div></header><section className="panel"><div className="searchResults">{links.map(([href,label])=><Link className="searchItem" href={href} key={href}>{label}</Link>)}</div></section></>}
