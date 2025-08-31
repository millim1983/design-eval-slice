# design-eval-slice (Vertical Slice)
- FastAPI 백엔드: LMM 해석 스텁 + RAG(키워드 검색) + Rubric 폼 데이터
- 실행:
  1) cd backend
  2) python -m venv .venv && .\.venv\Scripts\Activate.ps1
  3) pip install -r requirements.txt
  4) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  5) http://localhost:8000/docs
- Docker: backend/에서 `docker compose up --build`

## LLaVA Local Provider

Set environment variables when running the backend to use a local LLaVA model:

- `ANALYSIS_PROVIDER=llava_local`
- `LLAVA_MODEL_PATH` – path to the downloaded LLaVA model and processor.
- `LLAVA_DEVICE` – optional torch device (e.g. `cpu`, `cuda`, `cuda:0`).
  Defaults to GPU if available.
