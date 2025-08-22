import { AnalyzeFinding } from "../types";
export default function Findings({ items }:{ items:AnalyzeFinding[] }) {
  if (!items?.length) return <div className="muted">No findings yet.</div>;
  return (<div className="list">{items.map((f,i)=>(
    <div className="card" key={i}>
      <div className="row" style={{justifyContent:"space-between"}}>
        <b>{f.label}</b><span className="pill">conf {Math.round(f.confidence*100)}%</span>
      </div>
      <div className="muted">{f.explanation}</div>
      {f.citations?.length ? <div className="row" style={{marginTop:8}}>
        {f.citations.map(c=><span key={c} className="pill mono">{c}</span>)}
      </div> : null}
    </div>))}</div>);
}
