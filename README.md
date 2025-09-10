# Westfall Personal Assistant (Electron + Local Backend)
- Electron desktop UI.
- Python FastAPI backend runs locally (127.0.0.1), supervising llama.cpp via `llama-cpp-python`.
- First run: set `WESTFALL_MODEL_PATH` in a `.env` (use `.env.example`).
- Dev quickstart (local machine):
  1) Install Python 3.11 and Node 20+
  2) `pip install -r backend/requirements.txt`
  3) Run backend (dev): `python -m uvicorn westfall_backend.app:create_app --factory --host 127.0.0.1 --port 8756`
  4) Open Electron app (from `electron/`) with your local tooling; packaging can be added later.

### Releasing a beta (manual, no CI)
**Prereqs:** Node 20+, Python 3.11+, PyInstaller, electron-builder

1) **Package backend (PyInstaller)**
```bash
# from repo root
python -m venv .venv && . .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -r backend/requirements.txt pyinstaller
pyinstaller --name westfall-backend --onefile backend/westfall_backend/app.py
# outputs to dist/westfall-backend[.exe] → copy or move into dist-backend/
mkdir -p dist-backend && (cp dist/westfall-backend* dist-backend/ || copy dist\\westfall-backend.exe dist-backend\\)
```

2) **Build Electron installers**

```bash
cd electron
npm ci
# Windows
npx electron-builder --win nsis
# macOS
npx electron-builder --mac dmg
# Linux
npx electron-builder --linux AppImage deb
```

3) **Draft a Release (GitHub → Releases → Draft a new release)**

- Tag: v0.1.0-beta.1 (pre-release)
- Title: Westfall Assistant v0.1.0-beta.1
- Description: paste from .github/RELEASE_TEMPLATE.md

Upload artifacts from electron/dist/:

- Windows .exe
- macOS .dmg
- Linux .AppImage / .deb

Publish the pre-release.
