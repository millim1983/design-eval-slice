/// <reference types="vite/client" />
import type {
  UploadRequest,
  UploadResponse,
  AnalyzeRequest,
  AnalyzeResponse,
  ChatRequest,
  ChatResponse,
  RubricDSL,
  EvaluateRequest,
  EvaluateResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
async function j<TRes>(method: string, path: string, body?: any): Promise<TRes> {
  const r = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${method} ${path} -> ${r.status}`);
  return r.json();
}
export const api = {
  upload: (p: UploadRequest) => j<UploadResponse>("POST", "/uploads", p),
  analyze: (p: AnalyzeRequest) => j<AnalyzeResponse>("POST", "/analyze", p),
  chat: (p: ChatRequest) => j<ChatResponse>("POST", "/chat", p),
  search: (q: string) => j<any>("POST", "/search-guideline", { award_id: "aw_2025_kda", query: q }),
  rubric: () => j<RubricDSL>("GET", "/rubrics/aw_2025_kda/1.0.0"),
  evaluate: (rec: EvaluateRequest) => j<EvaluateResponse>("POST", "/evaluate", rec),
  report: (sid: string) => j<any>("GET", `/report/${sid}`),
};
export default api;
