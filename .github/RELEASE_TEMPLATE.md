# Westfall Assistant v0.1.0-beta.1

**What’s new**
- Electron desktop UI with local FastAPI backend
- llama.cpp via `llama-cpp-python` (GGUF) running locally
- Clean repo structure, environment-based config, and local-only networking

**Installers**
- Windows: `Westfall-Assistant-0.1.0-beta.1-win.exe`
- macOS: `Westfall-Assistant-0.1.0-beta.1-mac.dmg`
- Linux: `Westfall-Assistant-0.1.0-beta.1-linux.AppImage` (and/or `.deb`)

**First run**
1. Set a model path in `.env` (`WESTFALL_MODEL_PATH=...`), or use the app settings once exposed.
2. Launch the app; it starts a local backend on `127.0.0.1`.
3. Prompt and verify token streaming.

**Known limitations**
- No auto-update yet; manual download required
- Signing/notarization optional (dev builds)
