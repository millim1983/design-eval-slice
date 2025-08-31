from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import base64
import datetime
import json
import os
import re
import sqlite3
import time
from fastapi.responses import RedirectResponse

from app.ollama_client import generate

from app.core.paths import (
    SCHEMAS_DIR, SEEDS_DIR, DB_PATH,
    GUIDELINE_FILE, RUBRIC_FILE, ensure_dirs
)

app = FastAPI(title="Design Evaluation Vertical Slice", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def init_db():
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    sql = (SCHEMAS_DIR / "evidence_ledger.schema.sql").read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
    conn.close()

def log_evidence(kind: str, submission_id: str, payload: dict, user_id: str | None = None):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    conn.execute(
        "INSERT INTO evidence_ledger(kind, submission_id, user_id, at, payload_json) VALUES(?,?,?,?,?)",
        (kind, submission_id, user_id, now, json.dumps(payload, ensure_ascii=False))
    )
    conn.commit()
    conn.close()

def load_guideline_chunks():
    text = GUIDELINE_FILE.read_text(encoding="utf-8")
    chunks = []
    current = {"section_path": "Doc", "text": ""}
    for line in text.splitlines():
        if line.startswith("§") or line.startswith("# "):
            if current["text"].strip():
                chunks.append(current)
            current = {"section_path": line.strip(), "text": ""}
        else:
            current["text"] += line + "\\n"
    if current["text"].strip():
        chunks.append(current)
    for i, ch in enumerate(chunks):
        m = re.search(r"§([\\d\\.]+)", ch["section_path"])
        sec = m.group(1).replace(".", "_") if m else f"0_{i}"
        ch.update({
            "doc_id": "kda_2025_guideline_v1",
            "version": "1.0.0",
            "citation_id": f"cit_kda_v1_{sec}_{i:03d}"
        })
    return chunks

CHUNKS = []
RUBRIC = {}

def read_json_no_bom(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 여기서 기존 startup 작업 수행
    init_db()
    global CHUNKS, RUBRIC
    CHUNKS = load_guideline_chunks()
    RUBRIC = read_json_no_bom(RUBRIC_FILE)
    yield
    # 필요 시 종료(cleanup) 로직 작성 (지금은 없음)

# ⚠️ app 생성 시 lifespan 파라미터로 등록
app = FastAPI(title="Design Evaluation Vertical Slice", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])



def search_hits(query: str, top_k: int = 3):
    q = query.lower()
    scored = []
    for ch in CHUNKS:
        score = ch["text"].lower().count(q) + ch["section_path"].lower().count(q)
        if score > 0:
            scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = []
    for score, ch in scored[:top_k]:
        hits.append({
            "citation_id": ch["citation_id"],
            "doc_id": ch["doc_id"],
            "section_path": ch["section_path"],
            "excerpt": ch["text"].strip()[:240],
            "score": float(score),
            "version": ch["version"]
        })
    return hits

@app.post("/uploads")
def uploads(payload: dict):
    sid = f"sub_{int(time.time()*1000)}"
    out = {"submission_id": sid, "created_at": datetime.datetime.utcnow().isoformat() + "Z"}
    log_evidence("upload", sid, payload)
    return out

@app.post("/analyze")
def analyze(payload: dict):
    sid = payload.get("submission_id", "unknown")
    img_b64 = payload.get("image_base64")
    if not img_b64:
        raise HTTPException(status_code=400, detail="image_base64 required")
    image_bytes = base64.b64decode(img_b64.split(",")[-1])
    prompt = (
        "Analyze the design image and return a JSON array of findings. Each item "
        "must contain region {x,y,w,h} (0-1 float), label, confidence (0-1), "
        "explanation and citations (array)."
    )
    raw = generate(prompt, image_bytes)
    try:
        findings = json.loads(raw)
    except json.JSONDecodeError:
        hits = search_hits("contrast") or search_hits("대비")
        findings = [{
            "region": {"x": 0.18, "y": 0.22, "w": 0.42, "h": 0.28},
            "label": "Low Contrast",
            "confidence": 0.82,
            "explanation": "Text/background contrast may be below recommended ratio.",
            "citations": [h["citation_id"] for h in hits],
        }]
    resp = {
        "findings": findings,
        "model_version": os.getenv("OLLAMA_MODEL", "llava:7b"),
        "prompt_snapshot": prompt,
    }
    log_evidence("analyze", sid, resp)
    return resp

@app.post("/chat")
def chat(payload: dict):
    sid = payload.get("submission_id", "unknown")
    message = payload.get("message", "")
    needs_evidence = any(k in message.lower() for k in ["근거", "why", "guideline", "§", "contrast", "wcag"])
    citations = []
    if needs_evidence:
        citations = [h["citation_id"] for h in search_hits("contrast")]
    answer = "Contrast looks borderline. See guideline citations." if citations else \
             "General suggestion: improve visual hierarchy with size/weight/position."
    resp = {"answer": answer, "citations": citations, "model_version": "lmm_stub_v0", "prompt_snapshot": "Conversational QA prompt…"}
    log_evidence("chat", sid, {"message": message, **resp})
    return resp

@app.post("/search-guideline")
def search_guideline(payload: dict):
    q = payload.get("query", "")
    return {"hits": search_hits(q) if q else []}

@app.get("/rubrics/{award_id}/{version}")
def get_rubric(award_id: str, version: str):
    if RUBRIC.get("award_id") == award_id and RUBRIC.get("version") == version:
        return RUBRIC
    raise HTTPException(status_code=404, detail="Rubric not found")

@app.post("/evaluate")
def evaluate(record: dict):
    sid = record.get("submission_id", "unknown")
    log_evidence("evaluate", sid, record)
    return {"ok": True}

@app.get("/report/{submission_id}")
def report(submission_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT kind, at, payload_json FROM evidence_ledger WHERE submission_id=? ORDER BY id ASC", (submission_id,))
    items = [{"kind": k, "at": at, "payload": json.loads(p)} for (k, at, p) in cur.fetchall()]
    conn.close()
    return {"submission_id": submission_id, "events": items}

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")
