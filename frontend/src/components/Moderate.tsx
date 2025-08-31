import { useState } from "react";
import api from "../api";

export default function Moderate() {
  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    setResult("");
    try {
      const res = await api.moderate(input, output || undefined);
      setResult(res.compliant ? "compliant" : `blocked: ${res.reasons.join(",")}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <div className="row" style={{justifyContent:"space-between"}}>
        <b>Moderate</b>
        <button className="btn" onClick={run} disabled={busy || !input}>Check</button>
      </div>
      <input type="text" placeholder="Input" value={input} onChange={e=>setInput(e.target.value)} />
      <input type="text" placeholder="Output (optional)" value={output} onChange={e=>setOutput(e.target.value)} />
      {error && <div className="error">Error: {error}</div>}
      {result && <div className="row">결과: <span>{result}</span></div>}
    </div>
  );
}
