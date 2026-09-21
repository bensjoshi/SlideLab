import { useState } from 'react'
import './App.css'

interface Note {
  pitch: string
  midi: number
  start: number
  duration: number
  confidence: number
}

interface TranscriptionResult {
  notes: Note[]
  duration: number
  sample_rate: number
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [result, setResult] = useState<TranscriptionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null
    setFile(f)
    setResult(null)
    setError(null)
    setAudioUrl(f ? URL.createObjectURL(f) : null)
  }

  const handleTranscribe = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch('/api/transcribe', { method: 'POST', body: formData })
      if (!res.ok) {
        const detail = await res.json().catch(() => null)
        throw new Error(detail?.detail || `Server returned ${res.status}`)
      }
      const data: TranscriptionResult = await res.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const maxTime = result && result.duration > 0 ? result.duration : 1

  return (
    <div className="app">
      <header className="header">
        <h1>🎺 Trombone Transcription Platform</h1>
        <p className="subtitle">audio to notes</p>
      </header>

      <section className="upload-card">
        <label className="file-label">
          <input type="file" accept="audio/wav" onChange={handleFileChange} />
          {file ? file.name : 'Choose a .wav recording'}
        </label>

        {audioUrl && <audio controls src={audioUrl} className="player" />}

        <button className="transcribe-btn" onClick={handleTranscribe} disabled={!file || loading}>
          {loading ? 'Transcribing…' : 'Transcribe'}
        </button>

        {error && <p className="error">{error}</p>}
        {!file && (
          <p className="hint">
            No recording handy? Run <code>python generate_test_wav.py test.wav</code> in the
            backend folder to make one.
          </p>
        )}
      </section>

      {result && (
        <section className="results">
          <h2>
            Found {result.notes.length} note{result.notes.length === 1 ? '' : 's'} in{' '}
            {result.duration.toFixed(2)}s
          </h2>

          {result.notes.length > 0 && (
            <div className="piano-roll">
              {result.notes.map((n, i) => (
                <div
                  key={i}
                  className="note-bar"
                  title={`${n.pitch} @ ${n.start.toFixed(2)}s`}
                  style={{
                    left: `${(n.start / maxTime) * 100}%`,
                    width: `${Math.max((n.duration / maxTime) * 100, 0.6)}%`,
                    bottom: `${Math.min(Math.max(((n.midi - 40) / 40) * 100, 0), 92)}%`,
                  }}
                >
                  {n.pitch}
                </div>
              ))}
            </div>
          )}

          <table className="notes-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Pitch</th>
                <th>Start (s)</th>
                <th>Duration (s)</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {result.notes.map((n, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td>{n.pitch}</td>
                  <td>{n.start.toFixed(2)}</td>
                  <td>{n.duration.toFixed(2)}</td>
                  <td>{(n.confidence * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <footer className="footer">
        Pitch detection uses the YIN algorithm. Notes are grouped from raw pitch frames &mdash;
        rhythm quantisation and MusicXML export come in a later phase.
      </footer>
    </div>
  )
}

export default App
