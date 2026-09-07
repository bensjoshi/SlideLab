# Trombone Transcription Platform — MVP

From audio to sheet music, built for trombone. This is **Phase 1** of the
roadmap: a working end-to-end skeleton (upload audio → get notes) that
proves the pipeline before investing in a real transcription engine.

## What's actually here

- **`backend/`** — a FastAPI server with one real endpoint,
  `POST /api/transcribe`. It reads a WAV file, runs a simple
  autocorrelation pitch detector (`pitch.py`), and groups the pitch track
  into discrete notes (`notes.py`).
- **`frontend/`** — a React + TypeScript (Vite) app: upload a recording,
  hear it back, hit Transcribe, see the note sequence as a table and a
  simple piano-roll bar chart.

The pitch detection is deliberately simple — no ML dependencies, so
there's nothing to fight with getting it running. Roadmap Phase 2
("Real Transcription Engine") is where this gets swapped for something
more robust, and Phase 5 adds trombone-specific handling (glissando,
range checks, etc).

## Get it running

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python server.py
```

The server runs at `http://localhost:8000`. Confirm it's alive:

```bash
curl http://localhost:8000/api/health
```

Don't have a trombone recording on hand yet? Generate a synthetic test
tone so you can exercise the whole pipeline:

```bash
python generate_test_wav.py test.wav
```

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api/*` requests to
the backend on port 8000, so no CORS setup is needed locally.

### 3. Test the demo transcription

Upload `test.wav` (or a real recording) in the browser and click
**Transcribe**. You should see a handful of detected notes with their
start time, duration, and confidence.

## Key files to explore

```
backend/
  server.py       FastAPI app + /api/transcribe endpoint
  pitch.py         Autocorrelation pitch detection
  notes.py          Groups pitch frames into notes
  models.py          Shared Pydantic response models
  generate_test_wav.py  Makes a synthetic test recording

frontend/
  src/App.tsx     Upload UI, results table, piano-roll view
  src/App.css      Styling
  vite.config.ts    Dev proxy to the backend
```

## Known limitations (by design, for now)

- Only accepts `.wav` (mono or stereo, 8- or 16-bit PCM). Convert other
  formats with `ffmpeg` before uploading.
- Pitch detection is monophonic autocorrelation — good for a single
  trombone line, not accurate on chords, noisy recordings, or fast
  passages. This is intentional: MVP scope is to prove the pipeline
  works, not to nail accuracy yet.
- No persistence — nothing is saved between requests. Storage
  (PostgreSQL + object storage) comes in as part of the SaaS phase.
- No auth, rate limits, or deployment config yet — that's Phase 8.

## Next steps

Once this is running and you understand the codebase, the natural
next moves (per the roadmap) are:

1. Record 20–50 short trombone examples and hand-transcribe them —
   that becomes your golden dataset (Phase 3).
2. Replace `pitch.py`'s autocorrelation with a real pitch-tracking
   model and measure accuracy against that dataset (Phase 2).
3. Add rhythm quantisation and Music21/MusicXML export so output can
   open in notation software (Phase 4).
