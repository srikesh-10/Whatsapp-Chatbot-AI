from fastapi import FastAPI, File, UploadFile, HTTPException
import tempfile
import os
import shutil
from audio_converter import convert_to_wav
from transcriber import transcribe_audio

app = FastAPI(title="WhatsApp Voice Misinformation Detector", description="Audio to Text Module")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided.")
    
    # Extract extension
    _, ext = os.path.splitext(file.filename)
    if not ext:
        ext = ".bin"
        
    try:
        # Step 1: Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_input:
            shutil.copyfileobj(file.file, temp_input)
            input_path = temp_input.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_output:
            wav_path = temp_output.name

        # Step 2: Convert to wav
        convert_to_wav(input_path, wav_path)
        
        # Step 3: Run whisper transcription
        transcription_text = transcribe_audio(wav_path)
        
        # Step 4: Return JSON response
        return {"transcription": transcription_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temporary files to free space
        if 'input_path' in locals() and os.path.exists(input_path):
            os.remove(input_path)
        if 'wav_path' in locals() and os.path.exists(wav_path):
            os.remove(wav_path)
