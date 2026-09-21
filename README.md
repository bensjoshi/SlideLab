# Trombone Transcription Platform

From audio to sheet music, built for trombone. This covers **Phase 1**
(MVP web app) and **Phase 2** (real transcription engine) of the
roadmap.

## What's actually here

- **`backend/server.py`** — FastAPI server with one real endpoint,
  `POST /api/transcribe`.
- **`backend/transcription/`** — the actual transcription engine:
  - `audio.py` — WAV loading + preprocessing (DC offset removal, peak
    normalization, silence trimming)
  - `pitch.py` — pitch detection using the **YIN algorithm** (handles
    octave errors and imperfect tone much better than basic
    autocorrelation, no ML dependencies needed)
  - `notes.py` — groups the frame-by-frame pitch track into discrete
    notes
  - `cli.py` — run the whole pipeline from the command line, no server
    needed
- **`frontend/`** — React + TypeScript (Vite) app: upload a recording,
  hear it back, hit Transcribe, see the note sequence as a table and a
  simple piano-roll bar chart.

Why YIN and not CREPE (which the roadmap mentions as an example)? YIN
needs only numpy — nothing new to install — and is a well-established,
accurate algorithm in its own right. CREPE needs PyTorch/TensorFlow,
which is a much heavier install and worth reaching for once you have a
real dataset (Phase 3) to actually measure whether it improves
accuracy enough to justify the extra weight.

## Get it running

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python server.py
```

The server runs at `http://localhost:8000`. Confirm it's alive:

```bash
curl http://localhost:8000/api/health
```

Don't have a trombone recording on hand yet? Generate a synthetic test
tone:

```bash
python generate_test_wav.py test.wav
```

### 2. Try it from the command line (no server needed)

```bash
python -m transcription.cli test.wav
python -m transcription.cli test.wav --json out.json   # also save as JSON
```

This is the fastest way to check the pipeline is working, and useful
later for batch-testing against your golden dataset (Phase 3).

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api/*` requests
to the backend on port 8000, so no CORS setup is needed locally.

Upload `test.wav` (or a real recording) and click **Transcribe**.

## Key files to explore

```
backend/
  server.py                 FastAPI app + /api/transcribe endpoint
  requirements.txt
  generate_test_wav.py        Makes a synthetic test recording
  transcription/
    audio.py                    WAV loading + preprocessing
    pitch.py                     YIN pitch detection
    notes.py                      Groups pitch frames into notes
    models.py                      Shared Pydantic response models
    cli.py                          Standalone command-line runner

frontend/
  src/App.tsx                 Upload UI, results table, piano-roll view
  src/App.css                  Styling
  vite.config.ts                 Dev proxy to the backend
```

## Known limitations (by design, for now)

- Only accepts `.wav` (mono or stereo, 8- or 16-bit PCM). Convert other
  formats with `ffmpeg` before uploading.
- Pitch detection is monophonic — good for a single trombone line, not
  chords. YIN is meaningfully more accurate than plain autocorrelation
  but still isn't ML-model accuracy.
- No rhythm quantisation or MusicXML/PDF export yet — that's Phase 4.
- No persistence, auth, or deployment config yet — later SaaS phases.

## Next steps

1. Record 20–50 short trombone examples and hand-transcribe them —
   your golden dataset (Phase 3). Use `transcription/cli.py` to batch-run
   the pipeline against them and see where it's actually wrong.
2. Add rhythm quantisation and Music21/MusicXML export (Phase 4).
3. Add trombone-specific handling: range filtering, glissando
   detection, vibrato (Phase 5).
