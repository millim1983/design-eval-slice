import { useState } from "react";
import api from "../api";

export default function RagEval(){
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    setAnswer("");
    try {
      const res = await api.ragEval(query);
      setAnswer(res.answer);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const refresh = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.refreshRag();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <div className="row" style={{justifyContent:"space-between"}}>
        <b>RAG Eval</b>
        <div>
          <button className="btn" onClick={refresh} disabled={busy}>Refresh</button>
          <button className="btn" onClick={run} disabled={busy || !query}>Ask</button>
        </div>
      </div>
      <input type="text" placeholder="질문" value={query} onChange={e=>setQuery(e.target.value)} />
      {error && <div className="error">Error: {error}</div>}
      {answer && <div className="row">답변: <span>{answer}</span></div>}
    </div>
  );
}
