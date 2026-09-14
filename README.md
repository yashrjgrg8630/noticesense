# NoticeSense

NoticeSense analyses official notices and circulars with OCR and a configurable LLM provider. The production architecture separates the vanilla SPA frontend from the FastAPI backend:

- `static/` is built and deployed to Vercel.
- `backend/` runs as a container with Tesseract and Poppler installed.
- Ollama/Gemma 3 remains available for local development or a separately managed Ollama host.
- Gemini is an optional hosted provider, selected through configuration rather than hardcoded into deployment.

## Repository Layout

```text
static/                 Vanilla HTML/CSS/JS SPA
scripts/build-frontend.mjs  Static production build and API URL injection
backend/api/app.py      FastAPI entrypoint
backend/services/       OCR and parsing services
Dockerfile              Backend image with Tesseract and Poppler
vercel.json             Vercel static SPA configuration
requirements.txt        Python dependencies
.env.example            Local and production variable reference
```

## Local Development

### 1. Python environment

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install Tesseract OCR and Poppler on Windows as described by their installers. The existing Windows defaults in `backend/core/config.py` continue to work when those tools are installed in their standard locations. Set `TESSERACT_CMD` and `POPPLER_PATH` in `.env` when using custom locations.

### 2. Configure the provider

Copy `.env.example` to `.env` and choose one provider:

```env
LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

Then run Ollama and pull the model:

```powershell
ollama run gemma3:4b
```

For Gemini instead:

```env
LLM_BACKEND=gemini
GEMINI_API_KEY=your_key_here
```

If Ollama is selected but unavailable, upload and chat requests return an explicit configuration/runtime error.

### 3. Start FastAPI

```powershell
python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000`. FastAPI serves the SPA locally, so the frontend API URL remains same-origin when `VITE_API_URL` is empty.

The older Streamlit frontend remains available for local compatibility:

```powershell
python -m streamlit run frontend/app.py
```

## Frontend Deployment on Vercel

The repository contains a minimal Node build script; no frontend framework is required.

1. Import the repository into Vercel.
2. Set the Vercel environment variable `VITE_API_URL` to the public FastAPI URL, for example `https://api.example.com`.
3. Keep the project root at the repository root.
4. Deploy. `vercel.json` runs `npm run build`, copies `static/` to `dist/`, and injects the configured API URL into `dist/static/config.js`.

SPA navigation is handled by the rewrite in `vercel.json`. The frontend calls `${VITE_API_URL}/api/upload` and `${VITE_API_URL}/api/chat` in production, and same-origin `/api/*` locally.

To test the production build locally:

```powershell
$env:VITE_API_URL = "https://api.example.com"
npm.cmd run build
```

## Backend Deployment with Docker

Build and run the backend image:

```powershell
docker build -t noticesense-backend .
docker run --rm -p 8000:8000 --env-file .env noticesense-backend
```

The image installs:

- Python dependencies from `requirements.txt`
- `tesseract-ocr`
- `poppler-utils`

The container defaults are `/usr/bin/tesseract` and `/usr/bin` for those tools. Override `TESSERACT_CMD` or `POPPLER_PATH` only when the deployment image uses different locations. The container starts the existing application with `backend.api.app:app`.

A long-running single backend instance can use the current temporary filesystem and in-memory sessions. For multiple replicas, restarts, or durable notice history, production storage is still required: object storage for uploaded documents and a shared database or Redis-backed session store. This repository does not add a fake persistence layer.

## Environment Variables

See `.env.example` and `frontend/.env.example`. The important variables are:

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | Public FastAPI base URL used during the Vercel build; empty means same-origin locally |
| `CORS_ALLOWED_ORIGINS` | Comma-separated exact frontend origins allowed by FastAPI |
| `LLM_BACKEND` | `ollama` or `gemini` |
| `OLLAMA_BASE_URL` | Ollama server URL, normally `http://localhost:11434` locally |
| `OLLAMA_MODEL` | Ollama model name, normally `gemma3:4b` |
| `GEMINI_API_KEY` | Gemini key when `LLM_BACKEND=gemini` |
| `TESSERACT_CMD` | Tesseract executable path; container default is `/usr/bin/tesseract` |
| `POPPLER_PATH` | Poppler binary directory; container default is `/usr/bin` |
| `UPLOAD_DIR` | Temporary upload directory for one backend instance |

Do not commit `.env` or real API keys. Configure Vercel and backend service variables in their respective dashboards or secret stores.

## Production Ollama/Gemma 3

Ollama is not installed on Vercel and the Gemma model is not packaged into either deployment. To use Ollama in production, run Ollama on a separately managed machine or service that is reachable from the backend container, then set:

```env
LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://ollama.internal:11434
OLLAMA_MODEL=gemma3:4b
```

The backend uses that URL for both agent analysis and chat. Network access, model download, GPU capacity, authentication, and uptime for that Ollama service are external operational requirements.

## API Routes

- `GET /health`
- `POST /api/upload` with a PDF, PNG, JPG, or JPEG multipart file
- `POST /api/chat` with `session_id`, `message`, and optional chat history

The frontend is intentionally deployed separately from FastAPI. Vercel should host only the static SPA; the backend container owns OCR, parsing, agent calls, and API routes.
