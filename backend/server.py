"""
Trombone Transcription Platform - backend
Roadmap Phase 1 (MVP web server) + Phase 2 (real transcription engine)

Run it:
    pip install -r requirements.txt
    python server.py
    (or: uvicorn server:app --reload)

Then open http://localhost:8000/api/health to confirm it's alive, or
point the frontend at it. For quick command-line testing without the
server, see transcription/cli.py.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from transcription.audio import AudioLoadError, load_wav, preprocess
from transcription.models import TranscriptionResult
from transcription.notes import pitch_track_to_notes
from transcription.pitch import estimate_pitch_track

app = FastAPI(title="Trombone Transcription Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for local dev; lock this down before deploying
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "trombone-transcription"}


@app.post("/api/transcribe", response_model=TranscriptionResult)
async def transcribe(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".wav"):
        raise HTTPException(
            status_code=400,
            detail="Only .wav files are supported right now. Convert your recording to WAV first.",
        )

    raw = await file.read()
    try:
        audio, sample_rate = load_wav(raw)
    except AudioLoadError as e:
        raise HTTPException(status_code=400, detail=str(e))

    audio = preprocess(audio, sample_rate)
    duration = len(audio) / sample_rate if sample_rate else 0.0

    pitch_track = estimate_pitch_track(audio, sample_rate)
    detected_notes = pitch_track_to_notes(pitch_track)

    return TranscriptionResult(
        notes=detected_notes,
        duration=duration,
        sample_rate=sample_rate,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
