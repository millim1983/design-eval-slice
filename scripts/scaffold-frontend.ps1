# scripts/scaffold-frontend.ps1  (SAFE VERSION)
Param(
  [switch]$Force,
  [string]$Name   = "frontend",
  [string]$ApiBase = "http://localhost:8000"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-File {
  param([string]$Path, [string]$Content)
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force $dir | Out-Null }

  $isJson = [IO.Path]::GetExtension($Path).ToLower() -eq ".json"
  if ((Test-Path -LiteralPath $Path) -and -not $Force) {
    Write-Host "SKIP  $Path (exists; use -Force to overwrite)" -ForegroundColor Yellow
  } else {
    if ($isJson) {
      $enc = New-Object System.Text.UTF8Encoding($false) # ← No BOM
      [System.IO.File]::WriteAllText($Path, $Content, $enc)
    } else {
      Set-Content -LiteralPath $Path -Encoding utf8 -Value $Content
    }
    Write-Host "WRITE $Path" -ForegroundColor Green
  }
}



# --- repo root detection (robust) ---
$ScriptPath = $PSCommandPath; if (-not $ScriptPath) { $ScriptPath = $MyInvocation.MyCommand.Path }
$ScriptDir  = if ($ScriptPath) { Split-Path -Parent $ScriptPath } else { (Get-Location).Path }
$root       = (Resolve-Path (Join-Path $ScriptDir '..')).Path
$fe         = Join-Path $root $Name

if (Test-Path $fe) { Write-Host "Updating existing frontend at:  $fe" } else { Write-Host "Scaffolding new frontend at: $fe" }

# -------- files to write --------
$files = @()

$files += @{ path = Join-Path $fe "package.json"; content = @'
{
  "name": "design-eval-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": { "dev": "vite", "build": "tsc -b && vite build", "preview": "vite preview" },
  "dependencies": { "react": "^18.3.1", "react-dom": "^18.3.1" },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.4",
    "vite": "^5.3.4",
    "@vitejs/plugin-react": "^4.3.1"
  }
}
'@ }

$files += @{ path = Join-Path $fe "tsconfig.json"; content = @'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020","DOM","DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
'@ }

$files += @{ path = Join-Path $fe "vite.config.ts"; content = @'
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({ plugins: [react()], server: { port: 5173, host: true } });
'@ }

$files += @{ path = Join-Path $fe "index.html"; content = @'
<!doctype html><html lang="ko"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Design Eval Slice</title>
<style>
 body{font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial;margin:0;background:#0b1020;color:#eaf2ff}
 .wrap{max-width:980px;margin:24px auto;padding:16px}
 .card{background:#121833;border:1px solid #1f2750;border-radius:12px;padding:16px;margin:12px 0}
 .btn{background:#2a7fff;border:0;color:#fff;padding:10px 14px;border-radius:8px;cursor:pointer}
 .btn:disabled{opacity:.5;cursor:not-allowed}
 input,select,textarea{background:#0f152b;border:1px solid #283056;color:#eaf2ff;border-radius:8px;padding:8px}
 .row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
 .list{display:grid;gap:8px}
 .pill{background:#21305e;color:#a9c6ff;border:1px solid #2c3b72;border-radius:999px;padding:4px 10px;font-size:12px}
 .muted{opacity:.7}.mono{font-family:ui-monospace,Consolas,monospace}
</style></head><body>
<div id="root"></div><script type="module" src="/src/main.tsx"></script>
</body></html>
'@ }

$files += @{ path = Join-Path $fe ".env.development"; content = "VITE_API_BASE=$ApiBase`n" }

$files += @{ path = Join-Path $fe "src/main.tsx"; content = @'
import { createRoot } from "react-dom/client";
import App from "./App";
createRoot(document.getElementById("root")!).render(<App />);
'@ }

$files += @{ path = Join-Path $fe "src/types.ts"; content = @'
export type RubricDSL = {
  award_id: string; version: string;
  criteria: Array<{ id: string; label: string; description?: string;
    scale: { type: "int"|"float"|"enum"; min?: number; max?: number; enum?: string[] };
    weight: number; guideline_refs?: string[]; evidence_queries?: string[];
    required_checks?: string[]; visibility?: { show_model_suggestion_after_initial_score?: boolean }; }>;
  aggregation: { method: "weighted_mean"|"median"|"trimmed_mean"; outlier_policy?: string };
};
export type AnalyzeFinding = { region:{x:number;y:number;w:number;h:number}; label:string; confidence:number; explanation:string; citations?:string[]; };
export type AnalyzeResponse = { findings: AnalyzeFinding[]; model_version:string; prompt_snapshot:string; };
export type ReportEvent = { kind: string; at: string; payload: any };
'@ }

$files += @{ path = Join-Path $fe "src/api.ts"; content = @'
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
'@ }

$files += @{ path = Join-Path $fe "src/components/Findings.tsx"; content = @'
import { AnalyzeFinding } from "../types";
export default function Findings({ items }:{ items:AnalyzeFinding[] }) {
  if (!items?.length) return <div className="muted">No findings yet.</div>;
  return (<div className="list">{items.map((f,i)=>(
    <div className="card" key={i}>
      <div className="row" style={{justifyContent:"space-between"}}>
        <b>{f.label}</b><span className="pill">conf {Math.round(f.confidence*100)}%</span>
      </div>
      <div className="muted">{f.explanation}</div>
      {f.citations?.length ? <div className="row" style={{marginTop:8}}>
        {f.citations.map(c=><span key={c} className="pill mono">{c}</span>)}
      </div> : null}
    </div>))}</div>);
}
'@ }

$files += @{ path = Join-Path $fe "src/components/RubricForm.tsx"; content = @'
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
'@ }

$files += @{ path = Join-Path $fe "src/components/Report.tsx"; content = @'
import { ReportEvent } from "../types";
export default function Report({ events }:{ events: ReportEvent[] }) {
  if (!events?.length) return <div className="muted">No events yet.</div>;
  return (<div className="list">{events.map((e,i)=>(
    <div className="card" key={i}>
      <div className="row" style={{justifyContent:"space-between"}}>
        <b>{e.kind}</b><span className="muted mono">{e.at}</span>
      </div>
      <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(e.payload,null,2)}</pre>
    </div>))}</div>);
}
'@ }

$files += @{ path = Join-Path $fe "src/App.tsx"; content = @'
import { useEffect, useState } from "react";
import api from "./api";
import { RubricDSL, AnalyzeResponse, ReportEvent } from "./types";
import Findings from "./components/Findings";
import RubricForm from "./components/RubricForm";

export default function App(){
  const [sid, setSid] = useState<string>("");
  const [rubric, setRubric] = useState<RubricDSL|undefined>();
  const [findings, setFindings] = useState<AnalyzeResponse|undefined>();
  const [events, setEvents] = useState<ReportEvent[]>([]);
  const [busy, setBusy] = useState(false);

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
      {rubric && sid ? (<RubricForm rubric={rubric} submissionId={sid} onSubmitted={loadReport} />) : null}
      {sid ? (<div className="card">
        <div className="row" style={{justifyContent:"space-between"}}><b>3) Evidence Report</b><button className="btn" onClick={loadReport}>새로고침</button></div>
        <div className="muted">upload/analyze/evaluate 로그가 순서대로 보입니다.</div>
        <div style={{marginTop:8}} />
        {events.length ? events.map((e,i)=>(
          <div className="card" key={i} style={{background:"#0e1530"}}>
            <div className="row" style={{justifyContent:"space-between"}}><span className="pill">{e.kind}</span><span className="mono muted">{e.at}</span></div>
            <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(e.payload,null,2)}</pre>
          </div>
        )) : <div className="muted">아직 이벤트가 없습니다.</div>}
      </div>) : null}
    </div>
  );
}
'@ }

$files += @{ path = Join-Path $fe "Dockerfile"; content = @'
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm i
COPY . .
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
'@ }

$files += @{ path = Join-Path $fe "nginx.conf"; content = @'
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;
  location / { try_files $uri /index.html; }
  location /api/ { proxy_pass http://api:8000/; proxy_set_header Host $host; proxy_http_version 1.1; }
}
'@ }

# -------- write all --------
foreach ($f in $files) { Write-File -Path $f.path -Content $f.content }

# -------- .gitignore patch --------
$giPath = Join-Path $root ".gitignore"
$giAdd  = "`n# Frontend`n$Name/node_modules/`n$Name/dist/`n"
if (Test-Path -LiteralPath $giPath) {
  $gi = Get-Content -LiteralPath $giPath -Raw
  if ($gi -notmatch [regex]::Escape("$Name/node_modules/")) {
    Add-Content -LiteralPath $giPath -Value $giAdd
    Write-Host "APPEND .gitignore frontend entries"
  }
} else {
  Write-File -Path $giPath -Content "# Frontend`n$Name/node_modules/`n$Name/dist/`n"
}

Write-Host "`n✅ Frontend scaffold complete at: $fe"
Write-Host "Next:"
Write-Host "  cd `"$fe`"; npm install; npm run dev  # http://localhost:5173"
Write-Host "Docker (with backend):"
Write-Host "  docker compose up --build   # if docker-compose.yml includes web & api"
