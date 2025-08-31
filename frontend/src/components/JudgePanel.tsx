import { useState } from "react";
import api from "../api";
import { AnalyzeFinding } from "../types";

type Submission = { id: string; title: string };
type Props = { submissions: Submission[] };

export default function JudgePanel({ submissions }: Props) {
  const [sel, setSel] = useState<Submission | null>(null);
  const [findings, setFindings] = useState<AnalyzeFinding[]>([]);

  const select = async (s: Submission) => {
    setSel(s);
    // create a placeholder file for the analysis call
    const dummy = new File([""], "dummy.png", { type: "image/png" });
    try {
      const resp = await api.analyzeLLM(dummy, s.id);
      // allow judges to edit the explanation text
      setFindings(resp.findings || []);
    } catch (e) {
      console.error(e);
      setFindings([]);
    }
  };

  const updateExplanation = (idx: number, text: string) => {
    setFindings(fs => fs.map((f, i) => i === idx ? { ...f, explanation: text } : f));
  };

  return (
    <div className="card">
      <b>Judge Panel</b>
      <div className="row" style={{ alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          {submissions.map(s => (
            <div key={s.id} className="card" onClick={() => select(s)} style={{ cursor: "pointer", background: sel?.id === s.id ? "#0f142b" : undefined }}>
              {s.title}
            </div>
          ))}
        </div>
        <div style={{ flex: 2, marginLeft: 16 }}>
          {sel ? (
            <div>
              <h4>{sel.title}</h4>
              {findings.length ? findings.map((f, i) => (
                <div className="card" key={i}>
                  <div><b>{f.label}</b></div>
                  <textarea
                    style={{ width: "100%" }}
                    rows={3}
                    value={f.explanation}
                    onChange={e => updateExplanation(i, e.target.value)}
                  />
                </div>
              )) : <div className="muted">Run LLM analysis by selecting a submission.</div>}
            </div>
          ) : <div className="muted">Select a submission</div>}
        </div>
      </div>
    </div>
  );
}
