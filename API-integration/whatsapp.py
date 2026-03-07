from flask import Flask, request
import requests
from deep_translator import GoogleTranslator
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
audio_module = BASE_DIR / "Audio-to-text"
pipeline_module = BASE_DIR / "misinformation-detector" / "backend"

load_dotenv(BASE_DIR / ".env")

if str(audio_module) not in sys.path:
    sys.path.append(str(audio_module))
if str(pipeline_module) not in sys.path:
    sys.path.append(str(pipeline_module))

from audio_converter import convert_to_wav
from transcriber import transcribe_audio
from pipeline import run_pipeline


def _get_env(name: str) -> str:
    return os.getenv(name, "").strip()


TOKEN = _get_env("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = _get_env("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = _get_env("WHATSAPP_VERIFY_TOKEN")

app = Flask(__name__)


def _is_config_ready() -> bool:
    return all([TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN])


if not _is_config_ready():
    print(
        "Missing WhatsApp environment config. "
        "Set WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, and WHATSAPP_VERIFY_TOKEN in .env."
    )


@app.route("/webhook", methods=["GET"])
def verify():
    if not VERIFY_TOKEN:
        return "Server config missing VERIFY_TOKEN", 500

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    if not _is_config_ready():
        return "Server config missing WhatsApp credentials", 500

    data = request.json

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return "ok", 200

        message = value["messages"][0]
        sender = message["from"]

        if message["type"] != "audio":
            send_message(sender, "Please send a voice message.")
            return "ok", 200

        media_id = message["audio"]["id"]
        media_url = f"https://graph.facebook.com/v18.0/{media_id}"

        headers = {"Authorization": f"Bearer {TOKEN}"}

        media_response = requests.get(media_url, headers=headers).json()
        audio_url = media_response["url"]

        audio_data = requests.get(audio_url, headers=headers)

        with open("voice.opus", "wb") as f:
            f.write(audio_data.content)

        convert_to_wav("voice.opus", "voice.wav")
        speech_text = transcribe_audio("voice.wav")

        try:
            translated_text = GoogleTranslator(source="auto", target="en").translate(speech_text)
        except Exception:
            translated_text = speech_text

        verification_result = run_pipeline(translated_text)
        sources = verification_result.get("sources", [])[:3]
        source_lines = "\n".join(f"- {src}" for src in sources) if sources else "- No sources found"
        factcheck_report = f"""Claim: {verification_result.get("claim", translated_text)}
    Verdict: {verification_result.get("verdict", "UNCERTAIN")}
    Confidence: {verification_result.get("confidence", 0)}%
    Sources:
    {source_lines}

    Explanation:
    {verification_result.get("explanation", "")}

    {verification_result.get("counter_message", "")}
    """

        response_text = f"""Speech:
{speech_text}

English:
{translated_text}

{factcheck_report}
"""

        send_message(sender, response_text)

        os.remove("voice.opus")
        os.remove("voice.wav")

    except Exception as e:
        print(e)

    return "ok", 200


def send_message(phone, message):
    if not TOKEN or not PHONE_NUMBER_ID:
        raise RuntimeError("Cannot send WhatsApp message without token and phone number id")

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }

    requests.post(url, headers=headers, json=payload)


if __name__ == "__main__":
    app.run(port=5000)
