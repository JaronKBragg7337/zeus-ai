import { useEffect, useMemo, useState } from 'react'
import { Check, ClipboardCheck, RefreshCw, Sparkles, X } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

type Candidate = {
  id: string
  timestamp?: string
  source?: string
  status?: string
  instruction?: string
  ideal_output?: string
  metadata?: Record<string, unknown>
}

type ReviewLabel = 'success' | 'failed' | 'user_corrected' | 'bug' | 'unsafe' | 'unclear' | 'other'
type EvaluatorResult = {
  available: boolean
  score: number | null
  decision: string
  reason: string
}

const REVIEW_LABELS: ReviewLabel[] = ['success', 'failed', 'user_corrected', 'bug', 'unsafe', 'unclear', 'other']

export default function TrainingReviewPanel() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [label, setLabel] = useState<ReviewLabel>('success')
  const [notes, setNotes] = useState('')
  const [message, setMessage] = useState('')
  const [evaluator, setEvaluator] = useState<EvaluatorResult | null>(null)

  const selected = useMemo(
    () => candidates.find((candidate) => candidate.id === selectedId) || candidates[0],
    [candidates, selectedId]
  )

  const fetchCandidates = async () => {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetch(`${API_BASE}/api/training/candidates?limit=100`)
      const data = await res.json()
      const nextCandidates = data.candidates || []
      setCandidates(nextCandidates)
      setSelectedId(nextCandidates[0]?.id || null)
      setLabel((nextCandidates[0]?.status as ReviewLabel) || 'success')
    } catch {
      setMessage('Training review is unavailable.')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchCandidates()
  }, [])

  const selectCandidate = (candidate: Candidate) => {
    setSelectedId(candidate.id)
    setLabel((candidate.status as ReviewLabel) || 'success')
    setNotes('')
    setMessage('')
    setEvaluator(null)
  }

  const evaluateCandidate = async () => {
    if (!selected) return
    setMessage('')
    try {
      const res = await fetch(`${API_BASE}/api/training/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: selected.id }),
      })
      const data = await res.json()
      setEvaluator(data)
      if (data.decision && (REVIEW_LABELS as readonly string[]).includes(data.decision)) {
        setLabel(data.decision as ReviewLabel)
      }
    } catch {
      setMessage('Evaluator v1 could not score this candidate.')
    }
  }

  const reviewCandidate = async (approved: boolean) => {
    if (!selected) return
    setMessage('')
    try {
      const res = await fetch(`${API_BASE}/api/training/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: selected.id,
          approved,
          reviewer: 'desktop',
          label,
          notes,
        }),
      })
      if (!res.ok) throw new Error('review failed')
      setCandidates((prev) => prev.filter((candidate) => candidate.id !== selected.id))
      setSelectedId(null)
      setNotes('')
      setMessage(approved ? 'Approved for training.' : 'Rejected and kept for review history.')
    } catch {
      setMessage('Could not save review.')
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-3 border-b border-dark-800 bg-dark-900/50">
        <div className="flex items-center gap-3">
          <ClipboardCheck size={20} className="text-primary-400" />
          <div>
            <h2 className="text-sm font-semibold text-dark-100">Training Review</h2>
            <p className="text-xs text-dark-500">{candidates.length} pending examples</p>
          </div>
        </div>
        <button
          onClick={fetchCandidates}
          className="p-2 rounded-lg hover:bg-dark-800 text-dark-500 hover:text-dark-300 transition-all"
          title="Refresh"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </header>

      <div className="flex-1 min-h-0 grid grid-cols-[320px_1fr]">
        <aside className="border-r border-dark-800 overflow-y-auto p-4 space-y-2">
          {candidates.length === 0 ? (
            <div className="p-4 rounded-lg border border-dark-800 bg-dark-900/40">
              <p className="text-sm text-dark-300">No pending candidates.</p>
              <p className="text-xs text-dark-500 mt-1">New tool runs, corrections, and completions will appear here.</p>
            </div>
          ) : (
            candidates.map((candidate) => {
              const isSelected = selected?.id === candidate.id
              return (
                <button
                  key={candidate.id}
                  onClick={() => selectCandidate(candidate)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? 'border-primary-600 bg-primary-600/10'
                      : 'border-dark-800 bg-dark-900/40 hover:border-dark-700'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs text-primary-400">{candidate.source || 'unknown'}</span>
                    <span className="text-xs text-dark-500">{candidate.status || 'other'}</span>
                  </div>
                  <p className="mt-2 text-sm text-dark-200 line-clamp-3">{candidate.instruction || candidate.id}</p>
                </button>
              )
            })
          )}
        </aside>

        <section className="min-w-0 overflow-y-auto p-6">
          {selected ? (
            <div className="max-w-4xl space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-dark-100">{selected.source || 'candidate'}</h3>
                  <p className="text-xs text-dark-500">{selected.timestamp || selected.id}</p>
                </div>
                <select
                  value={label}
                  onChange={(event) => setLabel(event.target.value as ReviewLabel)}
                  className="bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-sm text-dark-200"
                >
                  {REVIEW_LABELS.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <div className="bg-dark-900/50 border border-dark-800 rounded-lg p-4">
                  <h4 className="text-xs font-semibold text-dark-400 mb-2">Instruction</h4>
                  <pre className="text-xs whitespace-pre-wrap break-words max-h-96 overflow-y-auto">{selected.instruction}</pre>
                </div>
                <div className="bg-dark-900/50 border border-dark-800 rounded-lg p-4">
                  <h4 className="text-xs font-semibold text-dark-400 mb-2">Candidate Output</h4>
                  <pre className="text-xs whitespace-pre-wrap break-words max-h-96 overflow-y-auto">{selected.ideal_output}</pre>
                </div>
              </div>

              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Review notes"
                className="w-full min-h-24 bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-sm text-dark-200 placeholder-dark-600 resize-y"
              />

              <div className="flex items-center gap-3">
                <button
                  onClick={() => reviewCandidate(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-500 transition-all"
                >
                  <Check size={16} />
                  Approve
                </button>
                <button
                  onClick={() => reviewCandidate(false)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600/15 text-red-300 border border-red-600/30 text-sm font-medium hover:bg-red-600/25 transition-all"
                >
                  <X size={16} />
                  Reject
                </button>
                <button
                  onClick={evaluateCandidate}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-dark-700 text-dark-200 text-sm font-medium hover:bg-dark-600 transition-all"
                >
                  <Sparkles size={16} />
                  Score
                </button>
                {message && <span className="text-xs text-dark-500">{message}</span>}
              </div>

              {evaluator && (
                <div className="bg-dark-900/50 border border-dark-800 rounded-lg p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h4 className="text-xs font-semibold text-dark-400">Evaluator v1</h4>
                    <span className="text-xs text-primary-400">
                      {evaluator.score === null ? 'untrained' : evaluator.score.toFixed(3)} · {evaluator.decision}
                    </span>
                  </div>
                  <p className="text-sm text-dark-300 mt-2">{evaluator.reason}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-sm text-dark-500">
              {loading ? 'Loading candidates...' : 'No candidate selected.'}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
