import { useState } from "react";
import api from "../api";

export default function VisionAnalyze() {
  const [file, setFile] = useState<File | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    setAnswer("");
    try {
      const res = await api.analyzeVision(file);
      setAnswer(res.answer);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <div className="row" style={{justifyContent:"space-between"}}>
        <b>Analyze Vision</b>
        <button className="btn" onClick={run} disabled={busy || !file}>Run</button>
      </div>
      <input type="file" accept="image/*" onChange={e=>setFile(e.target.files?.[0]??null)} />
      {error && <div className="error">Error: {error}</div>}
      {answer && <div className="row">답변: <span>{answer}</span></div>}
    </div>
  );
}
