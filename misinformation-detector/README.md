# WhatsApp Voice Misinformation Detector

An integrated hackathon project that verifies misinformation claims from voice/text using Whisper + internet evidence + semantic similarity, and displays clear results on a dashboard.

## Project Structure

```text
misinformation-detector/
  backend/
    whisper_module.py
    claim_verifier.py
    explanation_generator.py
    counter_message.py
    pipeline.py
    api.py
  frontend/
    index.html
    styles.css
    script.js
  requirements.txt
  README.md
  main.py
```

## Pipeline

Voice Message -> Whisper Speech-to-Text -> Claim Verifier -> Internet Evidence Search -> Semantic Similarity -> Verdict + Confidence -> Explanation -> Counter Message -> Dashboard

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Backend

From `misinformation-detector/backend`:

```bash
uvicorn api:app --reload
```

Backend URL:

- `http://127.0.0.1:8000`
- UI served at `http://127.0.0.1:8000/`

You can also run from project root:

```bash
python main.py
```

## API Endpoint

### POST `/verify`

Request:

```json
{
  "claim": "Drinking turmeric cures diabetes"
}
```

Response:

```json
{
  "claim": "Drinking turmeric cures diabetes",
  "verdict": "LIKELY FALSE",
  "confidence": 32,
  "sources": ["https://..."],
  "explanation": "...",
  "counter_message": "..."
}
```

### Optional Voice Endpoint

- `POST /verify-audio` with multipart file upload.

## Deployment

### Backend (Render/Railway)

Start command:

```bash
uvicorn api:app --host 0.0.0.0 --port 10000
```

Root directory for service: `misinformation-detector/backend`

#### Render Quick Setup

1. Create a new **Web Service** in Render and connect your repository.
2. Set **Root Directory** to `misinformation-detector/backend`.
3. Set **Build Command** to:

```bash
pip install -r ../requirements.txt
```

4. Set **Start Command** to:

```bash
uvicorn api:app --host 0.0.0.0 --port 10000
```

5. Add environment variable in Render:

```text
PYTHON_VERSION=3.11.9
```

6. Deploy and verify with:

```text
https://<your-render-service>.onrender.com/health
```

#### Railway Quick Setup

1. Create a new project from GitHub repo.
2. Set working directory to `misinformation-detector/backend`.
3. Use start command:

```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

### Frontend (Netlify/Vercel)

- Option 1: Deploy `frontend/` as static site and set `API_URL` in `script.js` to your backend URL.
- Option 2: Use backend-served UI at `/` from FastAPI.

#### Netlify Quick Setup

1. Create a new site from repository.
2. Set **Base directory** to `misinformation-detector/frontend`.
3. Set **Build command** empty (static site) and **Publish directory** to `.`.
4. In `frontend/script.js`, set API URL to deployed backend:

```js
const API_URL = "https://<your-render-service>.onrender.com/verify";
```

5. Redeploy frontend.

#### Vercel Quick Setup

1. Import repository into Vercel.
2. Set root directory to `misinformation-detector/frontend`.
3. Deploy as static site.
4. Update `API_URL` in `frontend/script.js` to backend public URL and redeploy.

## Demo Flow for Judges

1. User speaks a voice message.
2. Whisper converts speech to text.
3. Claim verifier searches the internet.
4. Semantic similarity computes likely truthfulness.
5. Dashboard shows claim, verdict, confidence, sources, and explanation.
6. Counter message is generated and can be copied/shared.

## Hackathon Demo Checklist

Before demo:

1. Backend `health` endpoint returns `{"status":"ok"}`.
2. Frontend loads without console errors.
3. `/verify` returns verdict and confidence for at least one sample claim.
4. Copy button works for counter message.
5. Chart updates after each verification.

Live demo script:

1. Enter a spoken-claim transcript in UI (or use voice endpoint if enabled).
2. Click **Run Verification**.
3. Show judges: claim, verdict, confidence, sources.
4. Highlight AI explanation and generated counter message.
5. Click **Copy Message** and paste it into notes/chat to prove usability.
