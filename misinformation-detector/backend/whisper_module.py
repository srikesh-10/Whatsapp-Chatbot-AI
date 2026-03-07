from pathlib import Path
from typing import Optional

import whisper

_MODEL: Optional[whisper.Whisper] = None


def _get_model() -> whisper.Whisper:
    global _MODEL
    if _MODEL is None:
        _MODEL = whisper.load_model("base")
    return _MODEL


def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file into text using Whisper."""
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    result = _get_model().transcribe(str(path))
    return result.get("text", "").strip()


def normalize_claim_text(claim_text: str) -> str:
    """Normalize direct text input for pipeline consistency."""
    return claim_text.strip()
