"""
Shared API models. Kept in their own module so both server.py and
notes.py can import Note without a circular import.
"""
from pydantic import BaseModel


class Note(BaseModel):
    pitch: str          # e.g. "Bb2"
    midi: int            # MIDI note number
    start: float          # seconds from start of audio
    duration: float        # seconds
    confidence: float       # 0.0-1.0, how sure the pitch detector was


class TranscriptionResult(BaseModel):
    notes: list[Note]
    duration: float
    sample_rate: int
