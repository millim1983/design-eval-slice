import { ReportEvent } from "../types";
export default function Report({ events }:{ events: ReportEvent[] }) {
  if (!events?.length) return <div className="muted">No events yet.</div>;
  return (<div className="list">{events.map((e,i)=>(
    <div className="card" key={i}>
      <div className="row" style={{justifyContent:"space-between"}}>
        <b>{e.kind}</b><span className="muted mono">{e.at}</span>
      </div>
      <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(e.payload,null,2)}</pre>
    </div>))}</div>);
}
