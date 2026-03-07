import whisper

# Load the base model globally so it's only loaded once when the application starts
model = whisper.load_model("base")

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes the given audio file using OpenAI Whisper.
    Returns the transcribed text.
    """
    result = model.transcribe(file_path)
    return result["text"].strip()
