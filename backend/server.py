"""
Trombone Transcription Platform - MVP backend
Roadmap Phase 1: Get the MVP Running

A minimal FastAPI server: upload a WAV recording, get back a note
sequence. The pitch detection here is intentionally simple (see
pitch.py) so the whole pipeline is easy to run and understand before
we invest in a real transcription engine (Phase 2) and trombone-
specific intelligence (Phase 5).

Run it:
    pip install -r requirements.txt
    python server.py
    (or: uvicorn server:app --reload)

Then open http://localhost:8000/api/health to confirm it's alive, or
point the frontend at it.
"""
import io
import wave

import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import TranscriptionResult
from pitch import estimate_pitch_track
from notes import pitch_track_to_notes

app = FastAPI(title="Trombone Transcription Platform - MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for local MVP; lock this down before deploying
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "trombone-transcription-mvp"}


@app.post("/api/transcribe", response_model=TranscriptionResult)
async def transcribe(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".wav"):
        raise HTTPException(
            status_code=400,
            detail="MVP only accepts .wav files for now. Convert your recording to WAV first.",
        )

    raw = await file.read()
    try:
        with wave.open(io.BytesIO(raw), "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_bytes = wf.readframes(n_frames)
    except wave.Error as e:
        raise HTTPException(status_code=400, detail=f"Could not read WAV file: {e}")

    audio = _decode_pcm(audio_bytes, sample_width, n_channels)
    duration = len(audio) / sample_rate if sample_rate else 0.0

    pitch_track = estimate_pitch_track(audio, sample_rate)
    detected_notes = pitch_track_to_notes(pitch_track)

    return TranscriptionResult(
        notes=detected_notes,
        duration=duration,
        sample_rate=sample_rate,
    )


def _decode_pcm(audio_bytes: bytes, sample_width: int, n_channels: int) -> np.ndarray:
    if sample_width == 2:
        dtype, max_val = np.int16, 32768.0
    elif sample_width == 1:
        dtype, max_val = np.uint8, 128.0
    else:
        raise HTTPException(
            status_code=400,
            detail="Only 8-bit or 16-bit WAV files are supported in the MVP.",
        )

    audio = np.frombuffer(audio_bytes, dtype=dtype).astype(np.float32)
    if sample_width == 1:
        audio -= 128.0
    audio /= max_val

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    return audio


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
