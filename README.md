# Westfall Personal Assistant (Electron + Local Backend)
- Electron desktop UI.
- Python FastAPI backend runs locally (127.0.0.1), supervising llama.cpp via `llama-cpp-python`.
- First run: set `WESTFALL_MODEL_PATH` in a `.env` (use `.env.example`).
- Dev quickstart (local machine):
  1) Install Python 3.11 and Node 20+
  2) `pip install -r backend/requirements.txt`
  3) Run backend (dev): `python -m uvicorn westfall_backend.app:create_app --factory --host 127.0.0.1 --port 8756`
  4) Open Electron app (from `electron/`) with your local tooling; packaging can be added later.
