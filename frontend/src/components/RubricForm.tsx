import { useMemo, useState } from "react";
import { RubricDSL } from "../types";
type Props = { rubric: RubricDSL; submissionId: string; onSubmitted: () => void; };
export default function RubricForm({ rubric, submissionId, onSubmitted }: Props) {
  const init = useMemo(()=>Object.fromEntries(rubric.criteria.map(c=>[c.id, (c.scale.min ?? 1)])),[rubric]);
  const [scores, setScores] = useState<Record<string, number>>(init);
  const [note, setNote] = useState<string>("");
  const setScore = (id:string, v:number)=> setScores(s=>({...s,[id]:v}));
  const submit = async () => {
    const rec = { submission_id: submissionId, judge_id: "u_demo_judge", rubric_version: rubric.version,
      scores: rubric.criteria.map(c=>({ criteria_id:c.id, score:Number(scores[c.id]||0), reason: note||undefined })) };
    const r = await fetch((import.meta as any).env.VITE_API_BASE || "http://localhost:8000" + "/evaluate",
      { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(rec) });
    if(!r.ok){ alert("Evaluate failed"); return; }
    onSubmitted();
  };
  return (<div className="card">
    <div className="row" style={{justifyContent:"space-between"}}>
      <b>Rubric • {rubric.award_id} <span className="pill">v{rubric.version}</span></b>
      <span className="muted">{rubric.criteria.length} criteria</span>
    </div>
    <div className="list">
      {rubric.criteria.map(c=>(
        <div key={c.id} className="card" style={{background:"#0f142b"}}>
          <div className="row" style={{justifyContent:"space-between"}}>
            <div><b>{c.label}</b>{c.description ? <div className="muted">{c.description}</div> : null}</div>
            {c.scale.type !== "enum" ? (
              <input type="range" min={c.scale.min ?? 1} max={c.scale.max ?? 5}
                     value={scores[c.id] ?? c.scale.min ?? 1}
                     onChange={e=>setScore(c.id, Number(e.target.value))} style={{width:220}} />
            ) : (
              <select value={scores[c.id] ?? 0} onChange={e=>setScore(c.id, Number(e.target.value))}>
                {c.scale.enum?.map((opt,i)=><option key={i} value={i}>{opt}</option>)}
              </select>
            )}
          </div>
        </div>
      ))}
      <div><label className="muted">공통 메모(선택)</label>
        <textarea rows={3} style={{width:"100%"}} value={note} onChange={e=>setNote(e.target.value)} />
      </div>
      <button className="btn" onClick={submit}>제출</button>
    </div>
  </div>);
}
