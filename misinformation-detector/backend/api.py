from pathlib import Path
import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests

from pipeline import run_pipeline
from whisper_module import transcribe_audio

app = FastAPI(title="WhatsApp Voice Misinformation Detector API")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerifyRequest(BaseModel):
    claim: str


def _send_whatsapp_message(phone: str, message: str) -> None:
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError("Missing WHATSAPP_TOKEN or WHATSAPP_PHONE_NUMBER_ID")

    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message},
    }
    requests.post(url, headers=headers, json=payload, timeout=20)


def _build_whatsapp_report(result: dict) -> str:
    sources = result.get("sources", [])[:3]
    source_lines = "\n".join(f"- {src}" for src in sources) if sources else "- No sources found"
    return (
        f"Claim: {result.get('claim', '')}\n"
        f"Verdict: {result.get('verdict', 'UNCERTAIN')}\n"
        f"Confidence: {result.get('confidence', 0)}%\n"
        f"Sources:\n{source_lines}\n\n"
        f"Explanation:\n{result.get('explanation', '')}\n\n"
        f"{result.get('counter_message', '')}"
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/webhook")
def verify_webhook(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    if not WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(status_code=500, detail="Server config missing WHATSAPP_VERIFY_TOKEN")

    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge) if hub_challenge.isdigit() else hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def whatsapp_webhook(payload: dict):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        raise HTTPException(status_code=500, detail="Server config missing WhatsApp credentials")

    try:
        value = payload["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return {"status": "ok"}

        message = value["messages"][0]
        sender = message["from"]

        if message.get("type") != "audio":
            _send_whatsapp_message(sender, "Please send a voice message.")
            return {"status": "ok"}

        media_id = message["audio"]["id"]
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

        media_info = requests.get(
            f"https://graph.facebook.com/v18.0/{media_id}",
            headers=headers,
            timeout=20,
        ).json()
        audio_url = media_info["url"]

        audio_response = requests.get(audio_url, headers=headers, timeout=30)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            temp_audio.write(audio_response.content)
            temp_path = temp_audio.name

        try:
            claim_text = transcribe_audio(temp_path)
            result = run_pipeline(claim_text)
            report = _build_whatsapp_report(result)
            _send_whatsapp_message(sender, report)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as exc:
        # Return 200 to avoid repeated webhook retries for malformed payloads.
        return {"status": "error", "message": str(exc)}

    return {"status": "ok"}


@app.post("/verify")
def verify(req: VerifyRequest) -> dict:
    try:
        return run_pipeline(req.claim)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification failed: {exc}") from exc


@app.post("/verify-audio")
async def verify_audio(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    temp_path = Path("temp_upload_audio")
    temp_path.write_bytes(await file.read())

    try:
        claim = transcribe_audio(str(temp_path))
        return run_pipeline(claim)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audio verification failed: {exc}") from exc
    finally:
        if temp_path.exists():
            temp_path.unlink()


frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="assets")


@app.get("/")
def serve_ui() -> FileResponse:
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)
