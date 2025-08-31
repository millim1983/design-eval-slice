const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
async function j(method: string, path: string, body?: any) {
  const r = await fetch(`${API_BASE}${path}`, { method, headers: { "Content-Type": "application/json" }, body: body?JSON.stringify(body):undefined });
  if (!r.ok) throw new Error(`${method} ${path} -> ${r.status}`);
  return r.json();
}
export const api = {
  upload: (p:{title:string;author_id:string;asset_url?:string;meta?:any}) => j("POST","/uploads",p),
  analyze: (submission_id:string) => j("POST","/analyze",{submission_id}),
  analyzeLlm: async (file: File, prompt: string, submissionId: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("prompt", prompt);
    fd.append("submission_id", submissionId);
    const r = await fetch(`${API_BASE}/analyze-llm`, { method: "POST", body: fd });
    if (!r.ok) throw new Error(`POST /analyze-llm -> ${r.status}`);
    return r.json();
  },
  search: (q:string) => j("POST","/search-guideline",{award_id:"aw_2025_kda", query:q}),
  rubric: () => j("GET","/rubrics/aw_2025_kda/1.0.0"),
  evaluate: (rec:any) => j("POST","/evaluate",rec),
  report: (sid:string) => j("GET",`/report/${sid}`)
};
export default api;
