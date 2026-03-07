# Audio to Text Module

This module handles the transcription of audio messages for the "WhatsApp Voice Misinformation Detector". It exposes a FastAPI endpoint that accepts audio files, converts them to `.wav` format using FFmpeg, and transcribes the audio using the open-source OpenAI Whisper model.

## Prerequisites

- **Python 3.8+**
- **FFmpeg**: You must have `ffmpeg` installed on your system.
  - Windows: `winget install ffmpeg` or download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt update && sudo apt install ffmpeg`

## Setup Instructions

1. **Navigate to the Directory**:
   ```bash
   cd "Whatsapp chatbot/Audio-to-text"
   ```

2. **Create a Virtual Environment** (Recommended):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

Start the FastAPI development server using `uvicorn`:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can also view the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

## Testing the Endpoint

The server exposes a single endpoint `POST /transcribe` which accepts a multipart form-data payload containing an audio file.

You can test using `curl`:

```bash
curl -X POST -F "file=@voice.mp3" http://127.0.0.1:8000/transcribe
```

### Expected Response Format

```json
{
 "transcription": "Drinking turmeric water cures diabetes"
}
```
