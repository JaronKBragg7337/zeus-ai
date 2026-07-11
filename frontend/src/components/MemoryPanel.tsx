import { useEffect, useState } from 'react'
import { Brain, Plus, Search, Trash2 } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

type Memory = {
  id: string
  content: string
  category: string
  source: string
  tags: string[]
  created_at: string
  updated_at: string
  last_used_at?: string | null
}

type MemoryStatus = {
  storage: string
  path: string
  memory_count: number
  categories: string[]
}

const categories = ['note', 'fact', 'preference', 'decision', 'project', 'instruction']

export default function MemoryPanel() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [status, setStatus] = useState<MemoryStatus | null>(null)
  const [query, setQuery] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('note')
  const [tags, setTags] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const refresh = async (nextQuery = query) => {
    const [statusResponse, memoriesResponse] = await Promise.all([
      fetch(`${API_BASE}/api/memory/status`),
      fetch(`${API_BASE}/api/memory?query=${encodeURIComponent(nextQuery)}`),
    ])
    if (!statusResponse.ok || !memoriesResponse.ok) throw new Error('Memory store is unavailable.')
    setStatus(await statusResponse.json())
    setMemories((await memoriesResponse.json()).memories || [])
  }

  useEffect(() => {
    void refresh('')
  }, [])

  const search = async () => {
    setLoading(true)
    setMessage('')
    try {
      await refresh(query)
    } catch (error) {
      setMessage((error as Error).message)
    }
    setLoading(false)
  }

  const addMemory = async () => {
    if (!content.trim()) return
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_BASE}/api/memory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          category,
          source: 'manual',
          tags: tags.split(',').map((tag) => tag.trim()).filter(Boolean),
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not save memory.')
      setContent('')
      setTags('')
      setCategory('note')
      await refresh(query)
      setMessage('Saved to local Zeus memory.')
    } catch (error) {
      setMessage((error as Error).message)
    }
    setLoading(false)
  }

  const removeMemory = async (memory: Memory) => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_BASE}/api/memory/${memory.id}`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Could not delete memory.')
      await refresh(query)
    } catch (error) {
      setMessage((error as Error).message)
    }
    setLoading(false)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-3 border-b border-dark-800 bg-dark-900/50">
        <div className="flex items-center gap-3">
          <Brain size={20} className="text-primary-400" />
          <div>
            <h2 className="text-sm font-semibold text-dark-100">Zeus Memory</h2>
            <p className="text-xs text-dark-500">{status?.memory_count || 0} saved memories, retrieved for relevant chats and agent tasks</p>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 max-w-5xl">
        <section className="border border-dark-800 bg-dark-900/40 rounded-lg p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_150px] gap-3">
            <textarea value={content} onChange={(event) => setContent(event.target.value)} rows={3} placeholder="Add a fact, preference, decision, project note, or instruction Zeus should remember..." className="bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-dark-200 placeholder-dark-600 resize-y focus:border-primary-600" />
            <div className="space-y-2">
              <select value={category} onChange={(event) => setCategory(event.target.value)} className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-dark-200">
                {categories.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
              <button onClick={() => void addMemory()} disabled={loading || !content.trim()} className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-md bg-primary-600 text-white text-sm hover:bg-primary-500 disabled:opacity-50"><Plus size={16} />Save memory</button>
            </div>
          </div>
          <input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="Tags, separated by commas (optional)" className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-dark-200 placeholder-dark-600 focus:border-primary-600" />
          <p className="text-xs text-dark-500 break-all">Stored locally: {status?.path || 'loading...'}. Zeus does not silently turn every chat into a memory.</p>
        </section>

        <section className="border border-dark-800 bg-dark-900/40 rounded-lg p-4">
          <div className="flex gap-2">
            <div className="relative flex-1"><Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-600" /><input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && void search()} placeholder="Search saved memories" className="w-full bg-dark-800 border border-dark-700 rounded-md pl-9 pr-3 py-2 text-sm text-dark-200 placeholder-dark-600 focus:border-primary-600" /></div>
            <button onClick={() => void search()} disabled={loading} className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-md text-sm disabled:opacity-50">Search</button>
          </div>
          {message && <p className="text-xs text-dark-400 mt-3">{message}</p>}
        </section>

        <section className="space-y-3">
          {memories.map((memory) => (
            <article key={memory.id} className="border border-dark-800 bg-dark-900/40 rounded-lg p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0"><div className="flex items-center gap-2 mb-2"><span className="text-xs text-primary-400">{memory.category}</span><span className="text-xs text-dark-600">{memory.source}</span></div><p className="text-sm text-dark-200 whitespace-pre-wrap break-words">{memory.content}</p></div>
                <button onClick={() => void removeMemory(memory)} disabled={loading} title="Delete memory" className="p-2 text-dark-500 hover:text-red-400 hover:bg-red-600/10 rounded-md"><Trash2 size={16} /></button>
              </div>
              {memory.tags.length > 0 && <div className="flex flex-wrap gap-1 mt-3">{memory.tags.map((tag) => <span key={tag} className="px-2 py-0.5 rounded-md bg-dark-800 text-dark-400 text-xs">{tag}</span>)}</div>}
            </article>
          ))}
          {memories.length === 0 && <p className="text-sm text-dark-600 px-1">No saved memories match this search.</p>}
        </section>
      </div>
    </div>
  )
}
