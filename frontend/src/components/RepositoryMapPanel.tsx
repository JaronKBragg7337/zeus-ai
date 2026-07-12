import { useEffect, useState } from 'react'
import { Download, Network, RefreshCw } from 'lucide-react'

const API_BASE = 'http://localhost:8000'
const DEFAULT_MANIFEST_URL = 'https://raw.githubusercontent.com/JaronKBragg7337/Summary-Of-repos-Memory-linker/main/repos.json'

type Status = {
  configured_manifest_url: string
  last_sync_at: string | null
  last_error: string | null
  repository_count: number
  summary_count: number
  artifact_root: string
  provenance_path: string
}

export default function RepositoryMapPanel() {
  const [status, setStatus] = useState<Status | null>(null)
  const [manifestUrl, setManifestUrl] = useState(DEFAULT_MANIFEST_URL)
  const [message, setMessage] = useState('')
  const [syncing, setSyncing] = useState(false)

  const loadStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/sources/repository-map/status`)
      if (!response.ok) throw new Error('Repository Map is unavailable.')
      const value = await response.json() as Status
      setStatus(value)
      setManifestUrl(value.configured_manifest_url || DEFAULT_MANIFEST_URL)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Repository Map is unavailable.')
    }
  }

  useEffect(() => { void loadStatus() }, [])

  const sync = async () => {
    setSyncing(true)
    setMessage('')
    try {
      const response = await fetch(`${API_BASE}/api/sources/repository-map/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manifest_url: manifestUrl, rebuild_index: true }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Repository Map sync failed.')
      setMessage(`Synced ${data.repository_count} repositories and ${data.summary_count} summaries into local Knowledge.`)
      await loadStatus()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Repository Map sync failed.')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <section className="h-full overflow-auto p-6 max-w-4xl">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="flex items-center gap-3"><Network size={20} className="text-primary-400" /><div><h2 className="text-sm font-semibold text-dark-100">Repository Map</h2><p className="text-xs text-dark-500">Verified project summaries imported as local, searchable knowledge</p></div></div>
        <button onClick={() => void loadStatus()} className="p-2 rounded-md text-dark-400 hover:text-dark-200 hover:bg-dark-800" title="Refresh status"><RefreshCw size={17} /></button>
      </div>

      <div className="border border-dark-800 bg-dark-900/40 rounded-lg p-4 space-y-4">
        <label className="block text-xs text-dark-400">Manifest URL<input value={manifestUrl} onChange={(event) => setManifestUrl(event.target.value)} className="mt-2 w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-dark-200" /></label>
        <button onClick={() => void sync()} disabled={syncing} className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-primary-600 text-white text-sm disabled:opacity-60"><Download size={16} />{syncing ? 'Syncing source...' : 'Sync and index'}</button>
        {message && <p className="text-sm text-dark-300">{message}</p>}
      </div>

      <div className="mt-5 border border-dark-800 bg-dark-900/40 rounded-lg p-4 text-sm space-y-2">
        <p className="text-dark-200">Last sync: <span className="text-dark-400">{status?.last_sync_at || 'Not synced yet'}</span></p>
        <p className="text-dark-200">Imported: <span className="text-dark-400">{status?.repository_count || 0} repositories, {status?.summary_count || 0} summaries</span></p>
        <p className="text-xs text-dark-500 break-all">Local artifacts: {status?.artifact_root}</p>
        <p className="text-xs text-dark-500 break-all">Provenance: {status?.provenance_path}</p>
        {status?.last_error && <p className="text-sm text-red-300">Last error: {status.last_error}</p>}
      </div>
    </section>
  )
}
