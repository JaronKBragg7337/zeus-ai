import { useEffect, useState } from 'react'
import type { ElementType } from 'react'
import { MessageSquare, Bot, FolderOpen, Brain, Database, Settings, Cpu, Power, RotateCcw, ClipboardCheck, BookOpen, Activity } from 'lucide-react'
import type { PanelType } from '../App'

interface SidebarProps {
  activePanel: PanelType
  onPanelChange: (panel: PanelType) => void
}

const navItems: { id: PanelType; label: string; icon: ElementType }[] = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'agent', label: 'Agent', icon: Bot },
  { id: 'files', label: 'Files', icon: FolderOpen },
  { id: 'rag', label: 'Documents', icon: Database },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
  { id: 'memory', label: 'Memory', icon: Brain },
  { id: 'heartbeat', label: 'Heartbeat', icon: Activity },
  { id: 'models', label: 'Models', icon: Brain },
  { id: 'training', label: 'Training Review', icon: ClipboardCheck },
]

const API_BASE = 'http://localhost:8000'

export default function Sidebar({ activePanel, onPanelChange }: SidebarProps) {
  const [stopRequested, setStopRequested] = useState(false)

  const refreshControlStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/control/status`)
      const data = await res.json()
      setStopRequested(Boolean(data.stop_requested))
    } catch {
      setStopRequested(false)
    }
  }

  useEffect(() => {
    refreshControlStatus()
  }, [])

  const toggleKillSwitch = async () => {
    const endpoint = stopRequested ? 'resume' : 'kill'
    try {
      await fetch(`${API_BASE}/api/control/${endpoint}`, { method: 'POST' })
      await refreshControlStatus()
    } catch {
      setStopRequested(false)
    }
  }

  const KillIcon = stopRequested ? RotateCcw : Power

  return (
    <aside className="w-16 flex flex-col items-center py-4 bg-dark-900 border-r border-dark-800">
      {/* Logo */}
      <div className="mb-6 p-2 rounded-xl bg-gradient-to-br from-primary-600 to-primary-800 shadow-lg">
        <Cpu size={24} className="text-white" />
      </div>

      {/* Nav */}
      <nav className="flex-1 flex flex-col gap-1">
        {navItems.map((item) => {
          const isActive = activePanel === item.id
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => onPanelChange(item.id)}
              className={`relative p-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-primary-600/20 text-primary-400'
                  : 'text-dark-500 hover:text-dark-300 hover:bg-dark-800/50'
              }`}
              title={item.label}
            >
              <Icon size={20} />
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-primary-500 rounded-r-full" />
              )}
              {/* Tooltip */}
              <span className="absolute left-14 px-2 py-1 bg-dark-800 text-dark-200 text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 border border-dark-700">
                {item.label}
              </span>
            </button>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="mt-auto flex flex-col gap-1">
        <button
          onClick={toggleKillSwitch}
          className={`p-3 rounded-xl transition-all ${
            stopRequested
              ? 'bg-emerald-600/15 text-emerald-400 hover:bg-emerald-600/25'
              : 'text-red-400 hover:text-red-300 hover:bg-red-600/10'
          }`}
          title={stopRequested ? 'Resume Zeus' : 'Stop Zeus'}
        >
          <KillIcon size={20} />
        </button>
        <button className="p-3 rounded-xl text-dark-500 hover:text-dark-300 hover:bg-dark-800/50 transition-all" title="Settings">
          <Settings size={20} />
        </button>
      </div>
    </aside>
  )
}
