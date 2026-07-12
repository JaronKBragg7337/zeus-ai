import { useEffect, useState } from 'react'
import { BookOpen, RefreshCw, Search, Radio } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

type KnowledgeStatus = {
  knowledge_root: string
  indexed: boolean
  source_file_count: number
  files_indexed: number
  chunks: number
  built_at?: string
}

type KnowledgeMatch = {
  source: string
  category: string
  chunk_index: number
  score: number
  content: string
}

type WatchStatus = {
  enabled: boolean
  interval_seconds: number
  scheduler_active: boolean
  last_checked_at?: string
  last_indexed_at?: string
  rebuild_count: number
  last_error?: string
}

export default function KnowledgePanel() {
  const [status, setStatus] = useState<KnowledgeStatus | null>(null)
  const [watch, setWatch] = useState<WatchStatus | null>(null)
  const [query, setQuery] = useState('')
  const [matches, setMatches] = useState<KnowledgeMatch[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const fetchStatus = async () => {
    try {
      const [res, watchRes] = await Promise.all([
        fetch(`${API_BASE}/api/knowledge/status`),
        fetch(`${API_BASE}/api/knowledge/watch/status`),
      ])
      setStatus(await res.json())
      if (watchRes.ok) setWatch(await watchRes.json())
    } catch {
      setMessage('Knowledge status is unavailable.')
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const rebuildIndex = async () => {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/index`, { method: 'POST' })
      const data = await res.json()
      setMessage(`Indexed ${data.files_indexed || 0} files into ${data.chunks || 0} chunks.`)
      await fetchStatus()
    } catch {
      setMessage('Could not rebuild knowledge index.')
    }
    setLoading(false)
  }

  const searchKnowledge = async () => {
    if (!query.trim()) return
    setLoading(true)
    setMessage('')
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 8 }),
      })
      const data = await res.json()
      setMatches(data.matches || [])
      if (!data.matches?.length) {
        setMessage('No matching knowledge found.')
      }
    } catch {
      setMessage('Knowledge search failed.')
    }
    setLoading(false)
  }

  const configureWatch = async (enabled: boolean) => {
    setLoading(true)
    setMessage('')
    try {
      const res = await fetch(`${API_BASE}/api/knowledge/watch/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      })
      if (!res.ok) throw new Error('Knowledge watch configuration failed.')
      setWatch(await res.json())
      setMessage(enabled ? 'Knowledge watch is on. Changed source files will be indexed automatically.' : 'Knowledge watch is off.')
    } catch {
      setMessage('Could not change Knowledge watch.')
    }
    setLoading(false)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-3 border-b border-dark-800 bg-dark-900/50">
        <div className="flex items-center gap-3">
          <BookOpen size={20} className="text-primary-400" />
          <div>
            <h2 className="text-sm font-semibold text-dark-100">Zeus Knowledge</h2>
            <p className="text-xs text-dark-500">{status?.source_file_count || 0} local source files</p>
          </div>
        </div>
        <button
          onClick={rebuildIndex}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-primary-600 text-white text-xs font-medium hover:bg-primary-500 disabled:opacity-50 transition-all"
          disabled={loading}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Rebuild
        </button>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 max-w-5xl">
        <section className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Stat label="Indexed" value={status?.indexed ? 'yes' : 'no'} />
          <Stat label="Files" value={String(status?.files_indexed || 0)} />
          <Stat label="Chunks" value={String(status?.chunks || 0)} />
          <Stat label="Built" value={status?.built_at || 'never'} />
        </section>

        <section className="bg-dark-900/40 border border-dark-800 rounded-lg p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3"><Radio size={17} className={watch?.enabled ? 'text-emerald-400' : 'text-dark-600'} /><div><p className="text-sm text-dark-200">Automatic Knowledge watch</p><p className="text-xs text-dark-500">{watch?.enabled ? `Checks local source folders every ${watch.interval_seconds}s` : 'Manual indexing only'}{watch?.last_indexed_at ? ` · last indexed ${watch.last_indexed_at}` : ''}</p></div></div>
          <button onClick={() => void configureWatch(!watch?.enabled)} disabled={loading} className={`px-3 py-2 rounded-md text-xs font-medium disabled:opacity-50 ${watch?.enabled ? 'bg-emerald-600/15 text-emerald-300 border border-emerald-600/30' : 'bg-dark-800 text-dark-300 border border-dark-700'}`}>{watch?.enabled ? 'Watch on' : 'Watch off'}</button>
        </section>

        <section className="bg-dark-900/40 border border-dark-800 rounded-lg p-4">
          <p className="text-xs text-dark-500 mb-3 break-all">{status?.knowledge_root}</p>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-600" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') searchKnowledge()
                }}
                placeholder="Search local manuals, research, docs..."
                className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-9 pr-4 py-2 text-sm text-dark-200 placeholder-dark-600 focus:border-primary-600 transition-colors"
              />
            </div>
            <button
              onClick={searchKnowledge}
              disabled={loading || !query.trim()}
              className="px-4 py-2 rounded-lg bg-dark-700 text-dark-200 hover:bg-dark-600 disabled:opacity-50 text-sm transition-all"
            >
              Search
            </button>
          </div>
          {message && <p className="text-xs text-dark-500 mt-3">{message}</p>}
        </section>

        <section className="space-y-3">
          {matches.map((match, index) => (
            <article key={`${match.source}-${match.chunk_index}-${index}`} className="bg-dark-900/40 border border-dark-800 rounded-lg p-4">
              <div className="flex items-center justify-between gap-3 mb-2">
                <p className="text-xs text-primary-400 break-all">{match.source}</p>
                <span className="text-xs text-dark-500">{match.category} · {match.score.toFixed(3)}</span>
              </div>
              <p className="text-sm text-dark-200 whitespace-pre-wrap break-words">{match.content}</p>
            </article>
          ))}
        </section>
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-dark-900/40 border border-dark-800 rounded-lg p-3">
      <p className="text-xs text-dark-500">{label}</p>
      <p className="text-sm text-dark-100 mt-1 truncate">{value}</p>
    </div>
  )
}
