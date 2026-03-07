from flask import Flask, request
import requests
import whisper
from deep_translator import GoogleTranslator
import os

TOKEN = "EAARYg4aoR04BQ6ey5dPDROtQYxmBNqXcpxHOZAwMxkxoEWzj1ZCODSQfZCGUZB9yRKUFC6ZBZCeMHwFlfGZBs3tNWxXgT9nvzY8ElpYruGFhNxLK8Tone9tZBSSPq3yiA2Sut1uYLBZCaivbWXt2MZAXksu34PUlyZAWr8pSXftFZAc7JBowiEfDwZBs3GB7uylPp19OQHuOHLOrne58nZB7WvomCLc3Pc3zWdsICFEqm082EtURsXASR4H39keZCGDy06pgsGsCgB9zrztZCrUGZBH9UxIZBbbIfH"

PHONE_NUMBER_ID = "929329550274400"
VERIFY_TOKEN = "hello123"

app = Flask(__name__)

model = whisper.load_model("base")


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():

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

        os.system("ffmpeg -loglevel quiet -i voice.opus -ar 16000 voice.wav -y")

        result = model.transcribe("voice.wav")

        speech_text = result["text"].strip()

        translated_text = GoogleTranslator(source="auto", target="en").translate(speech_text)

        response_text = f"""Speech:
{speech_text}

English:
{translated_text}
"""

        send_message(sender, response_text)

        os.remove("voice.opus")
        os.remove("voice.wav")

    except Exception as e:
        print(e)

    return "ok", 200


def send_message(phone, message):

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