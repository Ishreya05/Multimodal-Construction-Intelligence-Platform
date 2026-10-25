# BuildScope AI — Construction Intelligence Platform

A full-stack demo application for construction-site safety review, crack triage, material estimation, cost planning, scheduling, architectural concept visualization, and indicative real-estate valuation.

> **Important:** This is a decision-support prototype, not a certified engineering, safety, quantity-surveying, architectural, or property-valuation system. Image findings and costs are illustrative. Have a qualified professional verify every safety concern, crack assessment, quantity, design, schedule, and valuation before acting on it. Do not use this prototype to certify a site as safe.

## Stack
- Python 3.9+ and FastAPI backend
- React + Vite frontend
- Optional OpenAI-compatible multimodal API for image/text analysis
- Pydantic request/response schemas, upload validation, JSON responses, tests

## Quick start

### 1. Backend
Python 3.9+ recommended. From the project root:

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive API documentation.

### 2. Frontend
In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (normally http://localhost:5173). The UI expects the API at `http://localhost:8000`; set `VITE_API_BASE_URL` in `frontend/.env` if needed.

### 3. Optional AI provider
Copy `backend/.env.example` to `backend/.env` and set `AI_API_KEY`, `AI_BASE_URL`, and `AI_MODEL` for an OpenAI-compatible chat-completions endpoint that supports image input. The key stays on the backend and must never be put in a `VITE_*` variable. Without a key, the app uses clearly labelled demo-mode analysis; this fallback does **not** perform actual computer vision and must not be treated as an image inspection.

## Features
- Image uploads (JPEG, PNG, WebP) with size/type checks; text and structured project details
- Safety / PPE / hazard review and crack triage with urgency, possible causes, and next steps
- Material quantity and indicative cost estimation
- Task schedule generation from project inputs
- Concept design brief / architectural visualization prompt (text output, not a rendered CAD drawing)
- Indicative real-estate valuation using supplied comparable values or a configurable area rate
- JSON-schema-backed API output, health endpoint, request validation, and tests
- Responsive dashboard and explicit demo-mode notices

## API endpoints
- `GET /health`
- `POST /api/analyze` — multipart images + text + structured project data
- `POST /api/estimate` — materials and indicative budget
- `POST /api/schedule` — task schedule
- `POST /api/valuation` — indicative valuation
- `POST /api/design-brief` — concept design brief

## Safety and limitations
- The demo heuristics are not vision models. For genuine image interpretation, configure a suitable multimodal model and validate its outputs.
- AI output is untrusted and validated against Pydantic schemas, but schema validation cannot guarantee factual accuracy.
- No structural calculations, code compliance, permits, contractor quotes, live market feeds, or geotechnical analysis are provided.
- Uploads are processed in memory and are not intentionally persisted. Configure production-grade auth, rate limiting, logging redaction, malware scanning, storage policy, HTTPS, and provider governance before deployment.
- Costs/rates are examples and should be edited for local prices, taxes, waste factors, and project specifications.

## Tests
```bash
cd backend
pip install -r requirements.txt
pytest
```
