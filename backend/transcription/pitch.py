"""
Pitch (fundamental frequency) estimation using the YIN algorithm.

Roadmap Phase 2: "Real Transcription Engine". This replaces the MVP's
plain autocorrelation detector with YIN, which handles octave errors
and imperfect tone (breath noise, slight buzz) far better - while
staying dependency-light (numpy only) rather than reaching straight
for a full ML model like CREPE, which needs PyTorch/TensorFlow. That's
a reasonable upgrade later, once accuracy against a real dataset
(Phase 3) shows it's actually needed.

Reference: de Cheveigne & Kawahara, "YIN, a fundamental frequency
estimator for speech and music" (2002).
"""
from dataclasses import dataclass

import numpy as np

# Trombone range is roughly E2 (~82 Hz) to Bb4 (~466 Hz); search a bit
# wider so we don't clip legitimate edge notes (pedal tones, high register).
MIN_FREQ_HZ = 60.0
MAX_FREQ_HZ = 700.0

FRAME_SIZE = 2048
HOP_SIZE = 512
YIN_THRESHOLD = 0.15  # lower = stricter about what counts as "pitched"
MIN_CONFIDENCE = 0.3


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

    for i in range(n_frames):
        start = i * HOP_SIZE
        frame = audio[start:start + FRAME_SIZE]
        if len(frame) < FRAME_SIZE:
            break
        f0, conf = _yin_frame(frame, sample_rate)
        freqs[i] = f0
        confs[i] = conf

    return PitchTrack(frequencies=freqs, confidences=confs, hop_seconds=hop_seconds)


def _yin_frame(frame: np.ndarray, sample_rate: int) -> tuple[float, float]:
    n = len(frame)
    rms = np.sqrt(np.mean(frame ** 2))
    if rms < 1e-4:
        return 0.0, 0.0

    min_tau = max(1, int(sample_rate / MAX_FREQ_HZ))
    max_tau = min(int(sample_rate / MIN_FREQ_HZ), n // 2)
    if max_tau <= min_tau:
        return 0.0, 0.0

    # Step 1: difference function - how well the signal matches a
    # shifted copy of itself at each candidate lag (period) tau
    diff = np.zeros(max_tau)
    for tau in range(1, max_tau):
        diff[tau] = np.sum((frame[:n - tau] - frame[tau:n]) ** 2)

    # Step 2: cumulative mean normalized difference function - this is
    # YIN's key trick over plain autocorrelation, and what fixes most
    # octave errors
    cmnd = np.ones(max_tau)
    running_sum = 0.0
    for tau in range(1, max_tau):
        running_sum += diff[tau]
        cmnd[tau] = diff[tau] * tau / running_sum if running_sum > 0 else 1.0

    # Step 3: find the first dip below threshold - that's the
    # fundamental period
    tau_est = None
    for tau in range(min_tau, max_tau - 1):
        if cmnd[tau] < YIN_THRESHOLD:
            while tau + 1 < max_tau and cmnd[tau + 1] < cmnd[tau]:
                tau += 1
            tau_est = tau
            break

    if tau_est is None:
        # No confident dip - fall back to the global minimum but let
        # the low confidence score flag it as unreliable
        tau_est = int(np.argmin(cmnd[min_tau:max_tau])) + min_tau

    # Step 4: parabolic interpolation for sub-sample precision
    tau_refined = float(tau_est)
    if 0 < tau_est < max_tau - 1:
        s0, s1, s2 = cmnd[tau_est - 1], cmnd[tau_est], cmnd[tau_est + 1]
        denom = s0 - 2 * s1 + s2
        if denom != 0:
            tau_refined = tau_est + 0.5 * (s0 - s2) / denom

    confidence = float(np.clip(1.0 - cmnd[tau_est], 0.0, 1.0))
    if confidence < MIN_CONFIDENCE:
        return 0.0, confidence

    freq = sample_rate / tau_refined if tau_refined > 0 else 0.0
    return freq, confidence
