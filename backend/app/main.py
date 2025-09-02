from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import json, re, time, sqlite3, datetime, base64, os, asyncio
from fastapi.responses import RedirectResponse
from langchain.agents import AgentExecutor
import logging

from app.schemas import (
    UploadResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    EvaluateRequest,
    EvaluateResponse,
    AnalyzeFinding,
    Region,
    VisionRequest,
    VisionResponse,
    RagEvalRequest,
    RagEvalResponse,
    RagCitation,
    ModerateRequest,
    ModerateResponse,
    LLMChatResponse,
    StructuredError,
    AgentAnswer,
)

from app.core.paths import (
    SCHEMAS_DIR, SEEDS_DIR, DB_PATH,
    GUIDELINE_FILE, RUBRIC_FILE, ensure_dirs
)

from app.providers import ProviderFactory, generate_structured
from app.rag import RagService
from app.agent import build_agent, run_agent
from app.security import mask_pii, detect_prompt_injection, filter_output
from pydantic import ValidationError
from langchain.output_parsers import PydanticOutputParser
from app.core.config import AppConfig, load_config
from app.observability import init_observability


def init_db():
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    for name in [
        "evidence_ledger.schema.sql",
        "projects.schema.sql",
        "submissions.schema.sql",
        "judges.schema.sql",
        "assignments.schema.sql",
    ]:
        sql = (SCHEMAS_DIR / name).read_text(encoding="utf-8")
        conn.executescript(sql)
    # Apply lightweight migrations if the table already exists without new columns
    cur = conn.execute("PRAGMA table_info(evidence_ledger)")
    cols = {row[1] for row in cur.fetchall()}
    if "raw_output" not in cols:
        conn.execute("ALTER TABLE evidence_ledger ADD COLUMN raw_output TEXT")
    if "image" not in cols:
        conn.execute("ALTER TABLE evidence_ledger ADD COLUMN image TEXT")
    conn.commit()
    conn.close()

def log_evidence(
    kind: str,
    submission_id: str,
    payload: dict,
    user_id: str | None = None,
    raw_output: str | None = None,
    image: str | None = None,
):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    conn.execute(
        "INSERT INTO evidence_ledger(kind, submission_id, user_id, at, payload_json, raw_output, image) VALUES(?,?,?,?,?,?,?)",
        (kind, submission_id, user_id, now, json.dumps(payload, ensure_ascii=False), raw_output, image)
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

# Loaded configuration
CONFIG: AppConfig | None = None
rag_service: RagService | None = None
agent_executor: AgentExecutor | None = None
rag_ready: bool = False


def read_json_no_bom(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 여기서 기존 startup 작업 수행
    init_db()
    global CHUNKS, RUBRIC, CONFIG, rag_service, agent_executor, rag_ready
    CONFIG = load_config()
    init_observability(CONFIG.observability)
    CHUNKS = load_guideline_chunks()
    RUBRIC = read_json_no_bom(RUBRIC_FILE)
    rag_service = RagService(
        CONFIG.rag.expert_url,
        CONFIG.rag.evaluation_url,
        CONFIG.rag.timeout,
    )
    rag_ready = False
    try:
        await rag_service.refresh()
        rag_ready = True
    except Exception:
        logging.exception("Failed to refresh RAG index")
    agent_executor = build_agent(rag_service, CONFIG.models)
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


@app.post("/rag-index/refresh")
async def rag_index_refresh():
    if rag_service is None or not rag_ready:
        raise HTTPException(status_code=503, detail="RAG not initialized")
    ok, err = await rag_service.refresh()
    if not ok:
        status = 502 if isinstance(err, RuntimeError) else 503
        raise HTTPException(status_code=status, detail=str(err))
    return {"ok": True}


@app.post("/rag-eval", response_model=RagEvalResponse)
async def rag_eval(payload: RagEvalRequest) -> RagEvalResponse:
    query = payload.query
    if detect_prompt_injection(query):
        raise HTTPException(status_code=400, detail="Prompt injection detected")
    sanitized_query = mask_pii(query)
    if rag_service is None or not rag_ready:
        raise HTTPException(status_code=503, detail="RAG not initialized")
    try:
        result = rag_service.query(sanitized_query)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if filter_output(json.dumps(result, ensure_ascii=False)):
        raise HTTPException(status_code=403, detail="Disallowed content")
    result = json.loads(mask_pii(json.dumps(result, ensure_ascii=False)))
    citations = [RagCitation(doc_id=s.get("doc_id", ""), text=s.get("text", "")) for s in result.get("sources", [])]
    return RagEvalResponse(answer=result.get("answer", ""), citations=citations)


@app.post("/rag-agent")
async def rag_agent_endpoint(payload: dict) -> dict[str, str]:
    """Run the LangChain agent to route ``query`` to tools."""
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query required")
    if detect_prompt_injection(query):
        raise HTTPException(status_code=400, detail="Prompt injection detected")
    sanitized_query = mask_pii(query)
    if agent_executor is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    try:
        result = await run_in_threadpool(lambda: run_agent(agent_executor, sanitized_query))
    except ValidationError as exc:
        err = StructuredError(error="Agent output validation failed")
        raise HTTPException(status_code=502, detail=err.model_dump()) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if filter_output(result.answer):
        raise HTTPException(status_code=403, detail="Disallowed content")
    answer = mask_pii(result.answer)
    return {"answer": answer}

@app.post("/uploads", response_model=UploadResponse)
async def uploads(
    title: str = Form("Unnamed"),
    author_id: str = Form("unknown"),
    file: UploadFile | None = File(None),
) -> UploadResponse:
    sid = f"sub_{int(time.time() * 1000)}"
    out = UploadResponse(
        submission_id=sid,
        created_at=datetime.datetime.utcnow(),
    )
    image_b64: str | None = None
    if file is not None:
        if file.content_type not in {"image/jpeg", "image/png"}:
            raise HTTPException(400, "Only JPEG/PNG images allowed")
        content = await file.read()
        if len(content) > 2 * 1024 * 1024:
            raise HTTPException(413, "Image too large")
        image_b64 = base64.b64encode(content).decode("utf-8")
    payload = {
        "title": title,
        "author_id": author_id,
        "filename": file.filename if file else None,
    }
    log_evidence(
        "upload",
        sid,
        payload,
        image=image_b64,
    )
    return out


@app.post("/analyze-vision", response_model=VisionResponse)
async def analyze_vision(
    file: UploadFile = File(...),
    prompt: str = Form("Describe the image"),
) -> VisionResponse:
    if detect_prompt_injection(prompt):
        raise HTTPException(status_code=400, detail="Prompt injection detected")
    sanitized_prompt = mask_pii(prompt)
    if file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(400, "Only JPEG/PNG images allowed")
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, "Image too large")
    image_b64 = base64.b64encode(content).decode("utf-8")
    provider_name = os.getenv("LLM_PROVIDER", "ollama")
    try:
        provider = ProviderFactory.get(provider_name)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    try:
        raw = await provider.generate(sanitized_prompt, "llava:7b", images=[image_b64])
    except HTTPException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    answer = raw.get("response", "").strip()
    if filter_output(answer):
        raise HTTPException(status_code=403, detail="Disallowed content in response")
    masked_answer = mask_pii(answer)
    return VisionResponse(answer=masked_answer, model_version=raw.get("model", "llava:7b"))


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    sid = payload.submission_id
    hits = search_hits("contrast") or search_hits("대비")
    findings = [
        AnalyzeFinding(
            region=Region(x=0.18, y=0.22, w=0.42, h=0.28),
            label="Low Contrast",
            confidence=0.82,
            explanation="Text/background contrast may be below recommended ratio.",
            citations=[h["citation_id"] for h in hits],
        )
    ]
    resp = AnalyzeResponse(
        findings=findings,
        model_version="lmm_stub_v0",
        prompt_snapshot="Analyze visual hierarchy, contrast, typography…",
    )
    raw_output = resp.model_dump_json(ensure_ascii=False)
    log_evidence("analyze", sid, resp.model_dump(), raw_output=raw_output)
    return resp


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    sid = payload.submission_id
    message = payload.message
    if detect_prompt_injection(message):
        raise HTTPException(status_code=400, detail="Prompt injection detected")
    sanitized_message = mask_pii(message)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT image FROM evidence_ledger WHERE submission_id=? AND kind='upload' ORDER BY id DESC LIMIT 1",
        (sid,),
    )
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Image not found for submission")
    image_b64 = row[0]
    provider_name = os.getenv("LLM_PROVIDER", "ollama")
    try:
        provider = ProviderFactory.get(provider_name)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    parser = PydanticOutputParser(pydantic_object=LLMChatResponse)
    prompt = f"{sanitized_message}\n{parser.get_format_instructions()}"
    start_time = time.monotonic()
    logging.info("generate_structured start")
    try:
        parsed, raw = await generate_structured(
            provider,
            prompt,
            "llava:7b",
            parser,
            images=[image_b64],
            stream=False,
            timeout=60,
        )
    except HTTPException as exc:
        logging.info(
            "generate_structured failed in %.2f seconds",
            time.monotonic() - start_time,
        )
        if exc.status_code == 504:
            raise HTTPException(status_code=504, detail=exc.detail)
        raise
    except (asyncio.TimeoutError, TimeoutError) as exc:
        logging.info(
            "generate_structured timed out in %.2f seconds",
            time.monotonic() - start_time,
        )
        raise HTTPException(status_code=504, detail="LLM call timed out") from exc
    except ValidationError as exc:
        logging.info(
            "generate_structured failed in %.2f seconds",
            time.monotonic() - start_time,
        )
        err = StructuredError(error="Model output validation failed")
        raise HTTPException(status_code=502, detail=err.model_dump()) from exc
    else:
        logging.info(
            "generate_structured completed in %.2f seconds",
            time.monotonic() - start_time,
        )
    answer = parsed.answer.strip()
    if filter_output(answer):
        raise HTTPException(status_code=403, detail="Disallowed content in response")
    masked_answer = mask_pii(answer)
    resp = ChatResponse(
        answer=answer,
        citations=parsed.citations,
        model_version=raw.get("model", "llava:7b"),
        prompt_snapshot=sanitized_message,
    )
    log_payload = resp.model_dump()
    log_payload["answer"] = masked_answer
    log_evidence(
        "chat",
        sid,
        {"message": sanitized_message, **log_payload},
        raw_output=mask_pii(json.dumps(raw, ensure_ascii=False)),
    )
    return resp


@app.post("/moderate", response_model=ModerateResponse)
def moderate(payload: ModerateRequest) -> ModerateResponse:
    reasons: list[str] = []
    if detect_prompt_injection(payload.input):
        reasons.append("prompt_injection")
    if payload.output and filter_output(payload.output):
        reasons.append("disallowed_output")
    return ModerateResponse(compliant=not reasons, reasons=reasons)

@app.post("/search-guideline")
def search_guideline(payload: dict):
    q = payload.get("query", "")
    return {"hits": search_hits(q) if q else []}


# --- Project & Judging Management Endpoints ---

@app.post("/projects")
def create_project(payload: dict):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    conn = sqlite3.connect(DB_PATH)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    cur = conn.execute(
        "INSERT INTO projects(name, created_at) VALUES(?, ?)",
        (name, now)
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"project_id": pid, "name": name, "created_at": now}


@app.get("/projects")
def list_projects():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT id, name, created_at FROM projects ORDER BY id ASC")
    rows = [dict(project_id=i, name=n, created_at=c) for (i, n, c) in cur.fetchall()]
    conn.close()
    return {"projects": rows}


@app.post("/projects/{project_id}/submissions")
def create_submission(project_id: int, payload: dict):
    title = payload.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    conn = sqlite3.connect(DB_PATH)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    cur = conn.execute(
        "INSERT INTO submissions(project_id, title, created_at) VALUES(?, ?, ?)",
        (project_id, title, now)
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return {"submission_id": sid, "project_id": project_id, "title": title, "created_at": now}


@app.get("/projects/{project_id}/submissions")
def list_submissions(project_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT id, title, created_at FROM submissions WHERE project_id=? ORDER BY id ASC",
        (project_id,)
    )
    rows = [dict(submission_id=i, title=t, created_at=c) for (i, t, c) in cur.fetchall()]
    conn.close()
    return {"submissions": rows}


@app.post("/judges")
def create_judge(payload: dict):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    conn = sqlite3.connect(DB_PATH)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    cur = conn.execute(
        "INSERT INTO judges(name, created_at) VALUES(?, ?)",
        (name, now)
    )
    conn.commit()
    jid = cur.lastrowid
    conn.close()
    return {"judge_id": jid, "name": name, "created_at": now}


@app.get("/judges")
def list_judges():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT id, name, created_at FROM judges ORDER BY id ASC")
    rows = [dict(judge_id=i, name=n, created_at=c) for (i, n, c) in cur.fetchall()]
    conn.close()
    return {"judges": rows}


@app.post("/assignments")
def assign_judge(payload: dict):
    submission_id = payload.get("submission_id")
    judge_id = payload.get("judge_id")
    if not submission_id or not judge_id:
        raise HTTPException(status_code=400, detail="submission_id and judge_id required")
    conn = sqlite3.connect(DB_PATH)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    cur = conn.execute(
        "INSERT INTO assignments(submission_id, judge_id, created_at) VALUES(?, ?, ?)",
        (submission_id, judge_id, now)
    )
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return {"assignment_id": aid, "submission_id": submission_id, "judge_id": judge_id, "created_at": now}


@app.put("/assignments/{assignment_id}/score")
def record_score(assignment_id: int, payload: dict):
    score = payload.get("score")
    if score is None:
        raise HTTPException(status_code=400, detail="score required")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE assignments SET score=? WHERE id=?",
        (float(score), assignment_id)
    )
    conn.commit()
    conn.close()
    return {"assignment_id": assignment_id, "score": float(score)}


@app.get("/submissions/{submission_id}/final-score")
def final_score(submission_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT score FROM assignments WHERE submission_id=? AND score IS NOT NULL",
        (submission_id,)
    )
    scores = [row[0] for row in cur.fetchall() if row[0] is not None]
    conn.close()
    if not scores:
        return {"submission_id": submission_id, "final_score": None}
    avg = sum(scores) / len(scores)
    return {"submission_id": submission_id, "final_score": avg}

@app.get("/rubrics/{award_id}/{version}")
def get_rubric(award_id: str, version: str):
    if RUBRIC.get("award_id") == award_id and RUBRIC.get("version") == version:
        return RUBRIC
    raise HTTPException(status_code=404, detail="Rubric not found")

@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(record: EvaluateRequest) -> EvaluateResponse:
    sid = record.submission_id
    log_evidence("evaluate", sid, record.model_dump())
    return EvaluateResponse(ok=True)

@app.get("/report/{submission_id}")
def report(submission_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT kind, at, payload_json, raw_output, image FROM evidence_ledger WHERE submission_id=? ORDER BY id ASC",
        (submission_id,),
    )
    items = [
        {
            "kind": k,
            "at": at,
            "payload": json.loads(p),
            "raw_output": r,
            "image": img,
        }
        for (k, at, p, r, img) in cur.fetchall()
    ]
    conn.close()
    return {"submission_id": submission_id, "events": items}


@app.get("/dataset/export")
def dataset_export():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    dataset = []
    cur.execute("SELECT submission_id, image FROM evidence_ledger WHERE kind='upload'")
    uploads = cur.fetchall()
    for sid, image in uploads:
        cur.execute(
            "SELECT payload_json FROM evidence_ledger WHERE submission_id=? AND kind='analyze' ORDER BY id DESC LIMIT 1",
            (sid,),
        )
        row = cur.fetchone()
        findings = json.loads(row[0]).get("findings") if row else None
        cur.execute(
            "SELECT payload_json FROM evidence_ledger WHERE submission_id=? AND kind='evaluate' ORDER BY id DESC LIMIT 1",
            (sid,),
        )
        row = cur.fetchone()
        corrections = json.loads(row[0]) if row else None
        if image and findings and corrections:
            dataset.append({"image": image, "findings": findings, "corrections": corrections})
    conn.close()
    return {"data": dataset}

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")
