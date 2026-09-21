"""
Audio loading and preprocessing.

Roadmap Phase 2: "Implement audio preprocessing". Kept dependency-light
(stdlib `wave` + numpy only) so there's nothing new to install.
"""
import io
import wave

import numpy as np


class AudioLoadError(Exception):
    """Raised when the uploaded bytes can't be read as WAV audio."""


def load_wav(raw_bytes: bytes) -> tuple[np.ndarray, int]:
    """Decode WAV bytes into a mono float32 array in [-1, 1], plus sample rate."""
    try:
        with wave.open(io.BytesIO(raw_bytes), "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_bytes = wf.readframes(n_frames)
    except wave.Error as e:
        raise AudioLoadError(f"Could not read WAV file: {e}") from e

    if sample_width == 2:
        dtype, max_val = np.int16, 32768.0
    elif sample_width == 1:
        dtype, max_val = np.uint8, 128.0
    else:
        raise AudioLoadError("Only 8-bit or 16-bit WAV files are supported right now.")

    audio = np.frombuffer(audio_bytes, dtype=dtype).astype(np.float32)
    if sample_width == 1:
        audio -= 128.0
    audio /= max_val

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    return audio, sample_rate


def preprocess(audio: np.ndarray, sample_rate: int, trim_silence: bool = True) -> np.ndarray:
    """
    Clean up the raw signal before it hits the pitch detector:
    remove DC offset, normalize peak level, and optionally trim
    leading/trailing silence. Doesn't touch the actual pitch content.
    """
    if len(audio) == 0:
        return audio

    # Remove DC offset (common with cheap interfaces/mics)
    audio = audio - np.mean(audio)

    # Normalize so the loudest sample hits ~0.95, without amplifying
    # near-silent recordings into pure noise
    peak = np.max(np.abs(audio))
    if peak > 1e-6:
        audio = audio * (0.95 / peak)

    if trim_silence:
        audio = _trim_silence(audio, sample_rate)

    return audio


def _trim_silence(audio: np.ndarray, sample_rate: int, threshold: float = 0.02) -> np.ndarray:
    window = max(1, int(sample_rate * 0.02))  # 20ms windows
    n_windows = len(audio) // window
    if n_windows == 0:
        return audio

    energy = np.array([
        np.sqrt(np.mean(audio[i * window:(i + 1) * window] ** 2))
        for i in range(n_windows)
    ])
    loud = np.where(energy > threshold)[0]
    if len(loud) == 0:
        return audio  # entirely quiet - leave it, rather than return empty

    start = loud[0] * window
    end = min(len(audio), (loud[-1] + 1) * window)
    return audio[start:end]
