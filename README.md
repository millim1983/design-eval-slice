# design-eval-slice (Vertical Slice)
- FastAPI 백엔드: LMM 해석 스텁 + RAG(키워드 검색) + Rubric 폼 데이터
- 실행:
  1) `ollama serve` (LLaVA 서버 실행)
  2) `ollama run llava:7b` (모델 다운로드 확인)
  3) `export OLLAMA_URL=<OLLAMA 서버 URL>`
     - WSL: `http://<Windows 호스트 IP>:11434`
     - 네이티브: `http://localhost:11434`
  4) cd backend
  5) python -m venv .venv && .\.venv\Scripts\Activate.ps1
  6) pip install -r requirements.txt
  7) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  8) http://localhost:8000/docs
  9) `frontend/.env.example`을 `.env`로 복사하고 필요한 경우 `VITE_API_URL`을 수정
- Docker: backend/에서 `docker compose up --build`

## Configuration

Backend configuration is loaded from YAML files in `backend/config/` when the
application starts. Default sample files are provided:

- `models.yaml`
- `lora.yaml`
- `prompts.yaml`
- `policy.yaml`
- `rag.yaml`

Each file can be overridden by pointing an environment variable to an alternate
path:

```
MODELS_CONFIG=/path/to/models.yaml
LORA_CONFIG=/path/to/lora.yaml
PROMPTS_CONFIG=/path/to/prompts.yaml
POLICY_CONFIG=/path/to/policy.yaml
RAG_CONFIG=/path/to/rag.yaml
```

These files allow customizing model endpoints, LoRA adapters, prompts, security
policies, and RAG document sources without changing code.
