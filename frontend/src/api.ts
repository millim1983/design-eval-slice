const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
async function j(method: string, path: string, body?: any) {
  const r = await fetch(`${API_BASE}${path}`, { method, headers: { "Content-Type": "application/json" }, body: body?JSON.stringify(body):undefined });
  if (!r.ok) throw new Error(`${method} ${path} -> ${r.status}`);
  return r.json();
}
export const api = {
  upload: (p:{title:string;author_id:string;asset_url?:string;meta?:any}) => j("POST","/uploads",p),
  analyze: (submission_id:string) => j("POST","/analyze",{submission_id}),
  search: (q:string) => j("POST","/search-guideline",{award_id:"aw_2025_kda", query:q}),
  rubric: () => j("GET","/rubrics/aw_2025_kda/1.0.0"),
  evaluate: (rec:any) => j("POST","/evaluate",rec),
  report: (sid:string) => j("GET",`/report/${sid}`)
};
export default api;
