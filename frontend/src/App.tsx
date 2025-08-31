import { useEffect, useState } from "react";
import api from "./api";
import { ReportEvent } from "./types";
import RagEval from "./components/RagEval";
import VisionAnalyze from "./components/VisionAnalyze";
import Moderate from "./components/Moderate";

export default function App(){
  const [sid, setSid] = useState<string>("");
  const [events, setEvents] = useState<ReportEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [orgLog, setOrgLog] = useState<string[]>([]);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    if (!file) {
      setImageFile(null);
      return;
    }
    if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 2 * 1024 * 1024) {
      setError("Please select a JPEG or PNG image under 2MB.");
      e.target.value = "";
      setImageFile(null);
      return;
    }
    setError(null);
    setImageFile(file);
  };

  const start = async () => {
    setBusy(true);
    setError(null);
    setAnswer("");
    if (!imageFile) {
      setBusy(false);
      return;
    }
    let submissionId = "";
    try {
      const u = await api.upload({
        title: "Demo",
        author_id: "u_demo",
        file: imageFile,
      });
      submissionId = u.submission_id;
      setSid(submissionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
      return;
    }
    try {
      const c = await api.chat(submissionId, question);
      setAnswer(c.answer);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const loadReport = async () => { if(!sid) return; const rep = await api.report(sid); setEvents(rep.events ?? []); };
  useEffect(()=>{ if(sid) loadReport(); },[sid]);

  const organizerDemo = async () => {
    const log:string[] = [];
    const p = await api.createProject("Demo Project");
    log.push(`project ${p.project_id}`);
    const j = await api.createJudge("Judge One");
    log.push(`judge ${j.judge_id}`);
    const s = await api.createSubmission(p.project_id, "Demo Submission");
    log.push(`submission ${s.submission_id}`);
    const a = await api.assignJudge(s.submission_id, j.judge_id);
    log.push(`assignment ${a.assignment_id}`);
    await api.recordScore(a.assignment_id, 4.2);
    const fs = await api.finalScore(s.submission_id);
    log.push(`final ${fs.final_score}`);
    setOrgLog(log);
  };

  return (
    <div className="wrap">
      <h2>Design Evaluation Vertical Slice — <span className="muted">Frontend</span></h2>
      <div className="card">
        <div className="row" style={{justifyContent:"space-between"}}>
          <div><b>이미지 질문하기</b><div className="muted">이미지를 업로드하고 프롬프트로 질의합니다.</div></div>
          <button className="btn" onClick={start} disabled={busy || !imageFile}>Ask</button>
        </div>
        <input type="file" accept="image/*" onChange={onFileChange} />
        <input type="text" placeholder="프롬프트" value={question} onChange={e=>setQuestion(e.target.value)} />
        {error && <div className="error">Error: {error}</div>}
        {answer ? <div className="row">답변: <span>{answer}</span></div> : null}
      </div>
      {sid ? <div className="card"><div className="row">submission_id: <span className="mono pill">{sid}</span></div></div> : null}
      {sid ? (<div className="card">
        <div className="row" style={{justifyContent:"space-between"}}><b>4) Evidence Report</b><button className="btn" onClick={loadReport}>새로고침</button></div>
        <div className="muted">upload/analyze/evaluate 로그가 순서대로 보입니다.</div>
        <div style={{marginTop:8}} />
        {events.length ? events.map((e,i)=>(
          <div className="card" key={i} style={{background:"#0e1530"}}>
            <div className="row" style={{justifyContent:"space-between"}}><span className="pill">{e.kind}</span><span className="mono muted">{e.at}</span></div>
            <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(e.payload,null,2)}</pre>
          </div>
        )) : <div className="muted">아직 이벤트가 없습니다.</div>}
      </div>) : null}
      <div className="card">
        <div className="row" style={{justifyContent:"space-between"}}>
          <b>Organizer Demo</b>
          <button className="btn" onClick={organizerDemo}>Run</button>
        </div>
        {orgLog.length ? (
          <ul>
            {orgLog.map((l,i)=>(<li key={i} className="mono">{l}</li>))}
          </ul>
        ) : <div className="muted">No actions yet.</div>}
      </div>
      <VisionAnalyze />
      <Moderate />
      <RagEval />
    </div>
  );
}
