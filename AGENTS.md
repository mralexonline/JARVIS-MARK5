# Base44 Dev Environment

## What this app is
JARVIS-MARK5 — a Python **eel** desktop-style AI assistant. The user-facing UI is
HTML served by `eel` (`web/spider.html` is the entry, `web/home.html` is the rich
interface). `jarvis.py` is the entry point: it exposes `@eel.expose` functions the
frontend calls over a websocket bridge, and drives the AI/automation backend.

## Why it needs special handling to run here
The full backend (`backend/modules/automodel.py` → `llms.py`, `search.py`,
`OF/*`, `Powerpointer`, `speak`, …) pulls in desktop/ML deps that can't run
headless in a container: `pyautogui`, `opencv`, `chromadb`, `ollama`, `selenium`,
`groq`, `gradio_client`, `psycopg2`, `easyocr`/torch, plus Windows-only
(`pywin32`) and audio (`PyAudio`, `speech_recognition`) packages. It also needs a
running Postgres + Ollama + a `GROQ_API` key for the AI path.

To boot the UI in the preview without all that, `jarvis.py` was made
**import-tolerant**: the heavy desktop/ML imports are wrapped in `try/except` and
the Perplexica `docker compose` autostart is gated behind `START_PERPLEXICA=0`.
The eel web UI and its light exposed functions (`js_state`, `js_messages`,
`js_language`, `js_assistantname`, `js_page`, video/capture stubs) work
regardless. AI/automation (`Operate`) returns a clear "unavailable in headless
mode" message until the heavy deps + `GROQ_API` are provided.

A latent bug was also fixed: `jarvis.py` used `json` without importing it.

## Run it
```
docker compose -f docker-compose.base44.yml up -d --build
```
- Web UI on host port **3000** (eel/bottle, binds 0.0.0.0, `mode=None` so no
  browser is launched; `default_path='spider.html'` so `/` serves the UI).
- Source is bind-mounted; restart the `web` service to pick up Python edits
  (eel has no file watcher).
- Deps come from `requirements.base44.txt` (eel, mtranslate, python-dotenv) — the
  minimal set to serve the UI. The full `requirements.txt` is the desktop app's
  list and is NOT installed here.

## LLM providers (OpenAI / Anthropic)
- `backend/modules/llms/` is now a **package**: `__init__.py` is the original
  `llms.py` (Groq/Gradio/Ollama/Chroma/Postgres path — needs the full dep set), and
  `providers.py` adds OpenAI + Anthropic via `chat(provider, messages) -> str`
  (lazy-imports `openai`/`anthropic`, reads `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`
  from env). Existing `from backend.modules.llms import AIClient, pure_llama3`
  still works; `from backend.modules.llms.providers import chat` is the new entry.
- `openai` and `anthropic` are in `requirements.base44.txt`.

## Android Auto (simulated dashboard)
- `web/auto.html` is an in-browser Android Auto-style dashboard (navigation,
  media, phone, and a JARVIS assistant chat). Reach it from the landing page's
  "🚗 Android Auto Dashboard" button or directly at `/auto.html`.
- The assistant chat calls the new `@eel.expose js_llm_chat(provider, prompt)`
  in `jarvis.py`, which dispatches to `providers.chat` (ChatGPT / Claude). Voice
  input uses the Web Speech API and the existing `js_mic` bridge. Without API
  keys it returns a clear "key not set" message instead of crashing.

## Config / secrets
- `.env.base44-defaults` provides `InputLanguage`, `NickName`, `AssistantName`,
  `PORT`, and an empty `GROQ_API` placeholder so the app boots with no credentials.
- `GROQ_API` (Groq key, https://console.groq.com/keys) is the one external secret.
  Add it via the platform Secrets page; it's delivered to `/run/base44/app.env`
  and overrides the placeholder. Without it the UI still serves; AI calls won't.
- `ChatLog.json` (an empty `[]`) must exist — `LoadMessages()` reads it.

## Verify it works
```
curl -sf -H "Host: external-preview.example.com" http://localhost:3000/   # -> 200, JARVIS HTML
```
In the preview: the page title is "JARVIS Interface"; `eel.js_state()` returns
`"Available..."` and `eel.js_assistantname()` returns `"JARVIS"`.
