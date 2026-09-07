"""
Simple pitch (fundamental frequency) estimation.

MVP approach: frame-by-frame autocorrelation. This is not as accurate
as a real ML pitch model (see roadmap Phase 2: Real Transcription
Engine, which swaps this out for something like CREPE), but it needs
no ML dependencies and is good enough to prove the whole pipeline
works end-to-end: audio in -> notes out.
"""
from dataclasses import dataclass
import numpy as np

# Trombone range is roughly E2 (~82 Hz) to Bb4 (~466 Hz). We search a
# bit wider than that so we don't clip legitimate edge notes.
MIN_FREQ_HZ = 60.0
MAX_FREQ_HZ = 700.0

FRAME_SIZE = 2048
HOP_SIZE = 512

# Autocorrelation peaks below this normalized strength are treated as
# "no clear pitch" (silence, noise, breath sounds, etc).
CONFIDENCE_THRESHOLD = 0.3


@dataclass
class PitchTrack:
    frequencies: np.ndarray  # Hz per frame, 0.0 where no pitch was found
    confidences: np.ndarray  # 0.0-1.0 per frame
    hop_seconds: float


def estimate_pitch_track(audio: np.ndarray, sample_rate: int) -> PitchTrack:
    hop_seconds = HOP_SIZE / sample_rate
    n_frames = max(0, (len(audio) - FRAME_SIZE) // HOP_SIZE + 1)

    freqs = np.zeros(n_frames, dtype=np.float32)
    confs = np.zeros(n_frames, dtype=np.float32)
    window = np.hanning(FRAME_SIZE)

    for i in range(n_frames):
        start = i * HOP_SIZE
        frame = audio[start:start + FRAME_SIZE]
        if len(frame) < FRAME_SIZE:
            break
        f0, conf = _autocorrelate_frame(frame * window, sample_rate)
        freqs[i] = f0
        confs[i] = conf

    return PitchTrack(frequencies=freqs, confidences=confs, hop_seconds=hop_seconds)


def _autocorrelate_frame(frame: np.ndarray, sample_rate: int) -> tuple[float, float]:
    rms = np.sqrt(np.mean(frame ** 2))
    if rms < 1e-4:
        return 0.0, 0.0

    frame = frame - np.mean(frame)
    corr = np.correlate(frame, frame, mode="full")
    corr = corr[len(corr) // 2:]

    if corr[0] <= 0:
        return 0.0, 0.0

    min_lag = int(sample_rate / MAX_FREQ_HZ)
    max_lag = min(int(sample_rate / MIN_FREQ_HZ), len(corr) - 1)
    if max_lag <= min_lag:
        return 0.0, 0.0

    search = corr[min_lag:max_lag]
    if len(search) == 0:
        return 0.0, 0.0

    lag = int(np.argmax(search)) + min_lag
    confidence = float(corr[lag] / corr[0])

    if confidence < CONFIDENCE_THRESHOLD:
        return 0.0, confidence

    # Parabolic interpolation around the peak for a little extra precision
    if 0 < lag < len(corr) - 1:
        y0, y1, y2 = corr[lag - 1], corr[lag], corr[lag + 1]
        denom = y0 - 2 * y1 + y2
        if denom != 0:
            lag = lag + 0.5 * (y0 - y2) / denom

    freq = sample_rate / lag if lag > 0 else 0.0
    return float(freq), confidence
