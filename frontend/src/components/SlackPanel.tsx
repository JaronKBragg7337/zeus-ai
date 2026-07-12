import { useEffect, useState } from 'react'
import { KeyRound, MessageSquare, Plug, Trash2 } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

type SlackStatus = {
  state: string
  detail: string
  connected_at?: string | null
  bot_token_saved: boolean
  app_token_saved: boolean
  configured: boolean
}

export default function SlackPanel() {
  const [status, setStatus] = useState<SlackStatus | null>(null)
  const [botToken, setBotToken] = useState('')
  const [appToken, setAppToken] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const refresh = async () => {
    const response = await fetch(`${API_BASE}/api/connectors/slack/status`)
    if (!response.ok) throw new Error('Slack connector status is unavailable.')
    setStatus(await response.json())
  }

  useEffect(() => { void refresh().catch((error) => setMessage((error as Error).message)) }, [])

  const connect = async () => {
    if (!botToken.trim() && !appToken.trim()) return
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_BASE}/api/connectors/slack/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bot_token: botToken || undefined, app_token: appToken || undefined }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Slack configuration failed.')
      setBotToken('')
      setAppToken('')
      setStatus(data)
      setMessage(data.detail || 'Slack configuration saved locally.')
    } catch (error) {
      setMessage((error as Error).message)
    }
    setLoading(false)
  }

  const clear = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_BASE}/api/connectors/slack/config`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Could not remove local Slack credentials.')
      setStatus(await response.json())
    } catch (error) {
      setMessage((error as Error).message)
    }
    setLoading(false)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-3 border-b border-dark-800 bg-dark-900/50">
        <div className="flex items-center gap-3"><MessageSquare size={20} className="text-primary-400" /><div><h2 className="text-sm font-semibold text-dark-100">Slack Connector</h2><p className="text-xs text-dark-500">Direct messages through local Socket Mode</p></div></div>
        <span className={`px-2.5 py-1 rounded-md text-xs ${status?.state === 'connected' ? 'bg-emerald-600/15 text-emerald-300' : 'bg-dark-800 text-dark-400'}`}>{status?.state || 'checking'}</span>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-5 max-w-3xl space-y-5">
        <section className="border border-dark-800 bg-dark-900/40 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-3"><Plug size={18} className="text-primary-400 mt-0.5" /><div><p className="text-sm text-dark-200">{status?.detail || 'Checking local connector state...'}</p><p className="text-xs text-dark-500 mt-1">Bot token: {status?.bot_token_saved ? 'saved locally' : 'missing'} · App token: {status?.app_token_saved ? 'saved locally' : 'missing'}</p></div></div>
        </section>

        <section className="border border-dark-800 bg-dark-900/40 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2"><KeyRound size={16} className="text-primary-400" /><h3 className="text-sm font-medium text-dark-100">Local credentials</h3></div>
          <input type="password" autoComplete="off" value={botToken} onChange={(event) => setBotToken(event.target.value)} placeholder="Bot token starting xoxb-" className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-dark-200 placeholder-dark-600 focus:border-primary-600" />
          <input type="password" autoComplete="off" value={appToken} onChange={(event) => setAppToken(event.target.value)} placeholder="App token starting xapp-" className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-dark-200 placeholder-dark-600 focus:border-primary-600" />
          <div className="flex gap-2"><button onClick={() => void connect()} disabled={loading || (!botToken.trim() && !appToken.trim())} className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-primary-600 text-white text-sm hover:bg-primary-500 disabled:opacity-50"><Plug size={15} />Save and connect</button>{status?.configured && <button onClick={() => void clear()} disabled={loading} title="Remove locally stored Slack credentials" className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-red-600/15 text-red-300 text-sm hover:bg-red-600/25"><Trash2 size={15} />Remove local credentials</button>}</div>
          <p className="text-xs text-dark-500">Values are sent only to the local Zeus backend, saved in Windows Credential Manager, then cleared from this form. Zeus never displays them again.</p>
          {message && <p className="text-xs text-dark-300">{message}</p>}
        </section>

        <section className="border border-dark-800 bg-dark-900/40 rounded-lg p-4 text-sm text-dark-400 space-y-2"><p>Required Slack setup: Socket Mode enabled, app token with `connections:write`, bot scopes `chat:write`, `im:read`, and `im:history`, plus the `message.im` bot event.</p><p>When connected, a direct message to Zeus in Slack is saved as a local Zeus conversation and answered through the local Ollama model.</p></section>
      </div>
    </div>
  )
}
