"""
Standalone CLI for the transcription pipeline - no web server needed.
Useful for quickly checking a recording, or for scripting batch tests
against your golden dataset later (Phase 3).

Usage:
    python -m transcription.cli path/to/recording.wav
    python -m transcription.cli path/to/recording.wav --json out.json
"""
import argparse
import json
import sys

from transcription.audio import AudioLoadError, load_wav, preprocess
from transcription.notes import pitch_track_to_notes
from transcription.pitch import estimate_pitch_track


def transcribe_file(path: str):
    with open(path, "rb") as f:
        raw = f.read()

    try:
        audio, sample_rate = load_wav(raw)
    except AudioLoadError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    audio = preprocess(audio, sample_rate)
    duration = len(audio) / sample_rate if sample_rate else 0.0

    pitch_track = estimate_pitch_track(audio, sample_rate)
    notes = pitch_track_to_notes(pitch_track)

    return notes, duration, sample_rate


def main():
    parser = argparse.ArgumentParser(description="Transcribe a WAV recording to notes.")
    parser.add_argument("wav_file", help="Path to a .wav recording")
    parser.add_argument("--json", metavar="PATH", help="Also write results as JSON to this path")
    args = parser.parse_args()

    notes, duration, sample_rate = transcribe_file(args.wav_file)

    print(f"{args.wav_file}  ({duration:.2f}s @ {sample_rate}Hz)")
    print(f"{len(notes)} notes detected:\n")
    print(f"{'#':>3}  {'Pitch':<5} {'Start':>8} {'Dur':>8} {'Conf':>6}")
    for i, note in enumerate(notes, 1):
        print(f"{i:>3}  {note.pitch:<5} {note.start:>8.2f} {note.duration:>8.2f} {note.confidence:>6.0%}")

    if args.json:
        payload = {
            "duration": duration,
            "sample_rate": sample_rate,
            "notes": [n.model_dump() for n in notes],
        }
        with open(args.json, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
