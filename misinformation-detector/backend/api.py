from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline import run_pipeline
from whisper_module import transcribe_audio

app = FastAPI(title="WhatsApp Voice Misinformation Detector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerifyRequest(BaseModel):
    claim: str


@app.get("/health")
def health() -> dict:
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
