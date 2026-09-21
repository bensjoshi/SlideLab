"""
Convert a frame-by-frame pitch track into a discrete note sequence.

MVP-level approach: group consecutive frames that land on the same
MIDI pitch into a single note, and drop very short blips. Roadmap
Phase 4 (Full Transcription Pipeline) replaces this with real onset
detection and rhythm quantisation.
"""
import numpy as np

from transcription.models import Note
from transcription.pitch import PitchTrack

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

MIN_NOTE_DURATION_SECONDS = 0.06  # ignore blips shorter than this


def freq_to_midi(freq: float) -> int:
    return int(round(69 + 12 * np.log2(freq / 440.0)))


def midi_to_name(midi: int) -> str:
    name = NOTE_NAMES[midi % 12]
    octave = midi // 12 - 1
    return f"{name}{octave}"


def pitch_track_to_notes(pitch_track: PitchTrack) -> list[Note]:
    freqs = pitch_track.frequencies
    confs = pitch_track.confidences
    hop_seconds = pitch_track.hop_seconds

    notes: list[Note] = []
    current_midi = None
    current_start_frame = None
    current_confs: list[float] = []

    def flush(end_frame: int):
        nonlocal current_midi, current_start_frame, current_confs
        if current_midi is None:
            return
        start_time = current_start_frame * hop_seconds
        duration = (end_frame - current_start_frame) * hop_seconds
        if duration >= MIN_NOTE_DURATION_SECONDS:
            notes.append(
                Note(
                    pitch=midi_to_name(current_midi),
                    midi=current_midi,
                    start=round(start_time, 3),
                    duration=round(duration, 3),
                    confidence=round(float(np.mean(current_confs)), 3),
                )
            )
        current_midi = None
        current_start_frame = None
        current_confs = []

    for i, (f, c) in enumerate(zip(freqs, confs)):
        if f <= 0:
            flush(i)
            continue

        midi = freq_to_midi(f)

        if current_midi is None:
            current_midi = midi
            current_start_frame = i
            current_confs = [c]
        elif midi == current_midi:
            current_confs.append(c)
        else:
            flush(i)
            current_midi = midi
            current_start_frame = i
            current_confs = [c]

    flush(len(freqs))
    return notes
