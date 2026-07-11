import { useEffect, useState } from 'react'
import { Activity, Clock3, Play, RefreshCw } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

type HeartbeatStatus = {
  enabled: boolean
  interval_seconds: number
  running: boolean
  scheduler_active: boolean
  workspace: string
  last_run_at?: string | null
  last_reason?: string | null
  last_task_count: number
  run_count: number
}

type Observation = {
  id: string
  observed_at: string
  reason: string
  capabilities: { models: string[]; tool_count: number; full_computer_access: boolean }
  curiosity_tasks: Array<{ kind: string; task: string }>
}

const intervals = [300, 900, 1800, 3600, 14400]

const formatInterval = (seconds: number) => seconds < 3600 ? `${Math.round(seconds / 60)} min` : `${Math.round(seconds / 3600)} hr`

export default function HeartbeatPanel() {
  const [status, setStatus] = useState<HeartbeatStatus | null>(null)
  const [observations, setObservations] = useState<Observation[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const refresh = async () => {
    const [statusResponse, activityResponse] = await Promise.all([
      fetch(`${API_BASE}/api/heartbeat/status`),
      fetch(`${API_BASE}/api/heartbeat/activity?limit=8`),
    ])
    if (!statusResponse.ok || !activityResponse.ok) throw new Error('Heartbeat service is unavailable.')
    setStatus(await statusResponse.json())
    setObservations((await activityResponse.json()).observations || [])
  }

  useEffect(() => {
    void refresh().catch((error) => setMessage((error as Error).message))
    const timer = window.setInterval(() => void refresh().catch(() => undefined), 10_000)
    return () => window.clearInterval(timer)
  }, [])

  const configure = async (patch: Record<string, unknown>) => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_BASE}/api/heartbeat/config`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch),
      })
      if (!response.ok) throw new Error('Could not update heartbeat settings.')
      setStatus(await response.json())
      await refresh()
    } catch (error) {
      setMessage((error as Error).message)
    }
    setLoading(false)
  }

  const runNow = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_BASE}/api/heartbeat/run`, { method: 'POST' })
      if (!response.ok) throw new Error('Heartbeat observation failed.')
      const observation: Observation = await response.json()
      setMessage(`Observed ${observation.capabilities.models.length} models and created ${observation.curiosity_tasks.length} curiosity tasks.`)
      await refresh()
    } catch (error) {
      setMessage((error as Error).message)
    }
    setLoading(false)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between px-6 py-3 border-b border-dark-800 bg-dark-900/50">
        <div className="flex items-center gap-3"><Activity size={20} className="text-emerald-400" /><div><h2 className="text-sm font-semibold text-dark-100">Zeus Heartbeat</h2><p className="text-xs text-dark-500">Local observation and curiosity loop while Zeus is running</p></div></div>
        <button onClick={() => void runNow()} disabled={loading} className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-primary-600 text-white text-xs font-medium hover:bg-primary-500 disabled:opacity-50"><Play size={14} />Run now</button>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 max-w-5xl">
        <section className="border border-dark-800 bg-dark-900/40 rounded-lg p-4">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <Metric label="State" value={status?.running ? 'observing' : status?.enabled ? 'scheduled' : 'paused'} />
            <Metric label="Runs" value={String(status?.run_count || 0)} />
            <Metric label="Last tasks" value={String(status?.last_task_count || 0)} />
            <Metric label="Last run" value={status?.last_run_at ? new Date(status.last_run_at).toLocaleTimeString() : 'never'} />
          </div>
          <div className="flex flex-wrap items-center gap-3 mt-4">
            <button onClick={() => void configure({ enabled: !status?.enabled })} disabled={loading} className={`px-3 py-2 rounded-md text-sm ${status?.enabled ? 'bg-emerald-600/15 text-emerald-300 border border-emerald-600/30' : 'bg-dark-800 text-dark-400 border border-dark-700'}`}>{status?.enabled ? 'Heartbeat on' : 'Heartbeat off'}</button>
            <label className="flex items-center gap-2 text-xs text-dark-500"><Clock3 size={14} /><select value={status?.interval_seconds || 900} onChange={(event) => void configure({ interval_seconds: Number(event.target.value) })} disabled={loading} className="bg-dark-800 border border-dark-700 rounded-md px-2 py-2 text-dark-200">{intervals.map((seconds) => <option key={seconds} value={seconds}>{formatInterval(seconds)}</option>)}</select></label>
            <span className="text-xs text-dark-600 break-all">{status?.workspace}</span>
          </div>
          {message && <p className="text-xs text-dark-400 mt-3">{message}</p>}
        </section>

        <section className="space-y-3">
          {observations.map((observation) => (
            <article key={observation.id} className="border border-dark-800 bg-dark-900/40 rounded-lg p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3"><div><p className="text-sm text-dark-200">{new Date(observation.observed_at).toLocaleString()}</p><p className="text-xs text-dark-500">{observation.reason} · {observation.capabilities.models.length} models · {observation.capabilities.tool_count} tools</p></div><button title="Refresh" onClick={() => void refresh()} className="p-2 text-dark-500 hover:text-dark-200 hover:bg-dark-800 rounded-md"><RefreshCw size={14} /></button></div>
              <div className="space-y-2">{observation.curiosity_tasks.map((task, index) => <div key={`${task.kind}-${index}`} className="flex gap-3 text-sm"><span className="w-20 flex-shrink-0 text-xs text-primary-400 pt-0.5">{task.kind}</span><p className="text-dark-300">{task.task}</p></div>)}</div>
            </article>
          ))}
          {observations.length === 0 && <p className="text-sm text-dark-600">No heartbeat observation has been recorded yet.</p>}
        </section>
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="border border-dark-800 bg-dark-950/50 rounded-md p-3"><p className="text-xs text-dark-500">{label}</p><p className="text-sm text-dark-100 mt-1 truncate">{value}</p></div>
}
