from pathlib import Path
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Model Manager", version="0.1.0")
DATA_FILE = Path(__file__).resolve().parent.parent / "models.json"

def _read():
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def _write(data):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

class ModelIn(BaseModel):
    industry: str
    name: str
    version: str
    path: str
    active: bool = False

class ModelUpdate(BaseModel):
    version: str | None = None
    path: str | None = None
    active: bool | None = None

@app.get("/models")
def list_models():
    return _read()

@app.get("/models/{industry}")
def list_by_industry(industry: str):
    return [m for m in _read() if m["industry"] == industry]

@app.get("/models/{industry}/active")
def get_active(industry: str):
    for m in _read():
        if m["industry"] == industry and m.get("active"):
            return m
    raise HTTPException(404, "Active model not found")

@app.post("/models")
def register(meta: ModelIn):
    data = _read()
    data.append(meta.dict())
    _write(data)
    return meta

@app.put("/models/{industry}/{name}")
def update(industry: str, name: str, meta: ModelUpdate):
    data = _read()
    updated = False
    for m in data:
        if m["industry"] == industry and m["name"] == name:
            if meta.version is not None:
                m["version"] = meta.version
            if meta.path is not None:
                m["path"] = meta.path
            if meta.active is not None:
                m["active"] = meta.active
            updated = True
    if not updated:
        raise HTTPException(404, "Model not found")
    if meta.active:
        for m in data:
            if m["industry"] == industry and m["name"] != name:
                m["active"] = False
    _write(data)
    return {"status": "ok"}

@app.get("/stats")
def stats():
    data = _read()
    out = {}
    for m in data:
        out[m["industry"]] = out.get(m["industry"], 0) + 1
    return out
