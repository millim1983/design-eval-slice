import { useEffect, useState } from "react";
import api from "./api";
import { RubricDSL, AnalyzeResponse, ReportEvent } from "./types";
import Findings from "./components/Findings";
import RubricForm from "./components/RubricForm";
import JudgeReview from "./components/JudgeReview";

export default function App(){
  const [sid, setSid] = useState<string>("");
  const [rubric, setRubric] = useState<RubricDSL|undefined>();
  const [findings, setFindings] = useState<AnalyzeResponse|undefined>();
  const [events, setEvents] = useState<ReportEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [orgLog, setOrgLog] = useState<string[]>([]);

  const start = async () => {
    setBusy(true);
    const u = await api.upload({ title:"Demo", author_id:"u_demo", asset_url:"" });
    setSid(u.submission_id);
    const a = await api.analyze(u.submission_id);
    setFindings(a);
    const r = await api.rubric();
    setRubric(r);
    setBusy(false);
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
          <div><b>1) 업로드→해석→루브릭 불러오기</b><div className="muted">버튼 한 번으로 백엔드 수직슬라이스 호출</div></div>
          <button className="btn" onClick={start} disabled={busy}>Start Slice</button>
        </div>
        {sid ? <div className="row">submission_id: <span className="mono pill">{sid}</span></div> : null}
      </div>
      {findings ? (<div className="card"><b>2) 자동 분석 결과</b><Findings items={findings.findings} /></div>) : null}
      {findings && sid ? (<JudgeReview submissionId={sid} initialFindings={findings.findings} onSubmitted={loadReport} />) : null}
      {rubric && sid ? (<RubricForm rubric={rubric} submissionId={sid} onSubmitted={loadReport} />) : null}
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
    </div>
  );
}
