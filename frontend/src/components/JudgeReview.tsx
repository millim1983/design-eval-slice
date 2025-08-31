import { useState } from "react";
import api from "../api";
import { AnalyzeFinding } from "../types";

interface Props {
  submissionId: string;
  initialFindings: AnalyzeFinding[];
  onSubmitted?: () => void;
}

export default function JudgeReview({ submissionId, initialFindings, onSubmitted }: Props) {
  const [items, setItems] = useState<AnalyzeFinding[]>(initialFindings);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  const update = (index:number, field:keyof AnalyzeFinding, value:any)=>{
    setItems(fs => fs.map((f,i)=> i===index ? { ...f, [field]: value } : f));
  };

  const submit = async () => {
    setBusy(true);
    try {
      await api.evaluate({ submission_id: submissionId, findings: items, note });
      alert("Review submitted");
      onSubmitted?.();
    } catch (e) {
      alert("Submit failed");
    }
    setBusy(false);
  };

  if(!items?.length) return null;
  return (<div className="card">
    <div className="row" style={{justifyContent:"space-between"}}>
      <b>3) Judge Review</b>
      <button className="btn" onClick={submit} disabled={busy}>Submit to agency</button>
    </div>
    <div className="list">
      {items.map((f,i)=>(
        <div className="card" key={i} style={{background:"#0f142b"}}>
          <div><input value={f.label} onChange={e=>update(i,'label',e.target.value)} style={{width:"100%"}} /></div>
          <textarea rows={3} value={f.explanation} onChange={e=>update(i,'explanation',e.target.value)} style={{width:"100%",marginTop:4}} />
        </div>
      ))}
      <div><label className="muted">Notes</label>
        <textarea rows={3} style={{width:"100%"}} value={note} onChange={e=>setNote(e.target.value)} />
      </div>
    </div>
  </div>);
}
