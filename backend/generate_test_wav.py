"""
Generate a small synthetic WAV file so you can test the transcription
pipeline end-to-end before you have real trombone recordings.

Usage:
    python generate_test_wav.py test.wav
"""
import struct
import sys
import math
import wave

SAMPLE_RATE = 44100

# A short phrase roughly in the trombone's comfortable range:
# Bb2, D3, F3, Bb3
NOTES_HZ = [116.54, 146.83, 174.61, 233.08]
NOTE_DURATION = 0.6  # seconds
GAP_DURATION = 0.05  # seconds of silence between notes


def generate(path: str) -> None:
    samples = []
    for freq in NOTES_HZ:
        n_samples = int(SAMPLE_RATE * NOTE_DURATION)
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            # A few harmonics so it's not a pure, unrealistic sine tone
            value = 0.6 * math.sin(2 * math.pi * freq * t)
            value += 0.2 * math.sin(2 * math.pi * freq * 2 * t)
            value += 0.1 * math.sin(2 * math.pi * freq * 3 * t)
            samples.append(value)
        samples.extend([0.0] * int(SAMPLE_RATE * GAP_DURATION))

    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            s = max(-1.0, min(1.0, s))
            wf.writeframes(struct.pack("<h", int(s * 32767)))

    print(f"Wrote {len(samples) / SAMPLE_RATE:.2f}s of test audio to {path}")


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "test.wav"
    generate(out_path)
