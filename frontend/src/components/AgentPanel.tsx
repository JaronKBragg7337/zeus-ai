import { useState, useRef, useEffect } from 'react'
import { Play, Square, Bot, Terminal, FileCode, Search, Calculator, FolderTree, CheckCircle, AlertCircle } from 'lucide-react'

interface AgentPanelProps {
  selectedModel: string
}

interface AgentMessage {
  type: 'user' | 'status' | 'tool_call' | 'tool_result' | 'complete' | 'error'
  content: string
  name?: string
  parameters?: Record<string, unknown>
  result?: Record<string, unknown>
  timestamp: Date
}

const API_BASE = 'http://localhost:8000'

export default function AgentPanel({ selectedModel }: AgentPanelProps) {
  const [task, setTask] = useState('')
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [projectPath, setProjectPath] = useState('')
  const [maxSteps, setMaxSteps] = useState(10)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const runTask = async () => {
    if (!task.trim() || isRunning) return

    const userMsg: AgentMessage = { type: 'user', content: task.trim(), timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])
    setIsRunning(true)

    try {
      const response = await fetch(`${API_BASE}/api/agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: task.trim(),
          model: selectedModel,
          project_path: projectPath || undefined,
          max_steps: maxSteps
        })
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') {
                setIsRunning(false)
                return
              }
              try {
                const parsed = JSON.parse(data)
                const msg: AgentMessage = {
                  type: parsed.type,
                  content: parsed.message || parsed.name || '',
                  name: parsed.name,
                  parameters: parsed.parameters,
                  result: parsed.result,
                  timestamp: new Date()
                }
                setMessages(prev => [...prev, msg])
              } catch {
                // skip non-JSON lines
              }
            }
          }
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: `Failed: ${(err as Error).message}`,
        timestamp: new Date()
      }])
    } finally {
      setIsRunning(false)
    }
  }

  const getToolIcon = (name?: string) => {
    switch (name) {
      case 'read_file': return <FileCode size={14} />
      case 'write_file': return <FileCode size={14} />
      case 'list_files': return <FolderTree size={14} />
      case 'run_command': return <Terminal size={14} />
      case 'search_files': return <Search size={14} />
      case 'calculate': return <Calculator size={14} />
      case 'get_project_structure': return <FolderTree size={14} />
      default: return <Terminal size={14} />
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-dark-800 bg-dark-900/50">
        <div className="flex items-center gap-3">
          <Bot size={20} className="text-primary-400" />
          <div>
            <h2 className="text-sm font-semibold text-dark-100">AI Agent</h2>
            <p className="text-xs text-dark-500">Multi-step tasks with tool use</p>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-dark-500">
            <Bot size={48} className="mb-4 text-dark-700" />
            <p className="text-sm">Give me a task and I will use tools to complete it.</p>
            <div className="flex flex-wrap gap-2 mt-4 justify-center">
              {[
                'Analyze the project structure in C:\\myproject',
                'Find all TODO comments in my codebase',
                'Create a Python script that sorts files by type',
                'Check git status and suggest next steps',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setTask(suggestion)}
                  className="px-3 py-1.5 bg-dark-800 border border-dark-700 rounded-lg text-xs text-dark-400 hover:text-dark-200 hover:border-dark-600 transition-all"
                >
                  {suggestion.length > 50 ? suggestion.slice(0, 50) + '...' : suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className="animate-fade-in">
            {msg.type === 'user' && (
              <div className="flex gap-2 items-start">
                <div className="w-6 h-6 rounded-md bg-primary-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs text-white font-bold">U</span>
                </div>
                <div className="bg-dark-800 border border-dark-700/50 rounded-xl rounded-bl-md px-4 py-2.5 max-w-[85%]">
                  <p className="text-sm text-dark-200">{msg.content}</p>
                </div>
              </div>
            )}

            {msg.type === 'status' && (
              <div className="flex items-center gap-2 px-8 py-1">
                <div className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse" />
                <p className="text-xs text-dark-500">{msg.content}</p>
              </div>
            )}

            {msg.type === 'tool_call' && (
              <div className="flex gap-2 items-start ml-8">
                <div className="w-6 h-6 rounded-md bg-amber-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  {getToolIcon(msg.name)}
                </div>
                <div className="bg-amber-600/5 border border-amber-600/20 rounded-xl rounded-bl-md px-4 py-2.5 max-w-[85%]">
                  <p className="text-xs font-medium text-amber-400 mb-1">Using: {msg.name}</p>
                  {msg.parameters && (
                    <pre className="text-xs text-dark-400 bg-dark-900/50 rounded-lg p-2 overflow-x-auto">
                      {JSON.stringify(msg.parameters, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            )}

            {msg.type === 'tool_result' && (
              <div className="flex gap-2 items-start ml-8">
                <div className="w-6 h-6 rounded-md bg-emerald-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle size={14} className="text-emerald-400" />
                </div>
                <div className="bg-emerald-600/5 border border-emerald-600/20 rounded-xl rounded-bl-md px-4 py-2.5 max-w-[85%]">
                  <p className="text-xs font-medium text-emerald-400 mb-1">Result</p>
                  {msg.result && (
                    <pre className="text-xs text-dark-400 bg-dark-900/50 rounded-lg p-2 overflow-x-auto max-h-40 overflow-y-auto">
                      {typeof msg.result === 'string' ? msg.result : JSON.stringify(msg.result, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            )}

            {msg.type === 'complete' && (
              <div className="flex gap-2 items-start ml-8">
                <div className="w-6 h-6 rounded-md bg-primary-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle size={14} className="text-primary-400" />
                </div>
                <div className="bg-dark-800 border border-dark-700/50 rounded-xl rounded-bl-md px-4 py-2.5 max-w-[85%]">
                  <p className="text-sm text-dark-200 whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            )}

            {msg.type === 'error' && (
              <div className="flex gap-2 items-start">
                <div className="w-6 h-6 rounded-md bg-red-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <AlertCircle size={14} className="text-red-400" />
                </div>
                <div className="bg-red-600/5 border border-red-600/20 rounded-xl rounded-bl-md px-4 py-2.5">
                  <p className="text-sm text-red-400">{msg.content}</p>
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-dark-800 bg-dark-900/50 px-4 py-3">
        <div className="max-w-4xl mx-auto space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Project path (optional, e.g. C:\\myproject)"
              value={projectPath}
              onChange={(e) => setProjectPath(e.target.value)}
              className="flex-1 bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-xs text-dark-300 placeholder-dark-600 focus:border-primary-600 transition-colors"
            />
            <input
              type="number"
              placeholder="Max steps"
              value={maxSteps}
              onChange={(e) => setMaxSteps(Number(e.target.value))}
              min={1}
              max={50}
              className="w-24 bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-xs text-dark-300 focus:border-primary-600 transition-colors"
            />
          </div>
          <div className="flex gap-2">
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runTask() } }}
              placeholder="Describe a task for the AI agent... (e.g., 'Read the README in my project folder and summarize it')"
              className="flex-1 bg-dark-800 border border-dark-700 rounded-xl px-4 py-3 text-sm text-dark-200 placeholder-dark-500 resize-none focus:border-primary-600 transition-colors"
              rows={2}
              disabled={isRunning}
            />
            {isRunning ? (
              <button
                onClick={() => setIsRunning(false)}
                className="px-4 rounded-xl bg-red-600/20 text-red-400 hover:bg-red-600/30 transition-all flex-shrink-0"
              >
                <Square size={18} />
              </button>
            ) : (
              <button
                onClick={runTask}
                disabled={!task.trim()}
                className="px-4 rounded-xl bg-primary-600 text-white hover:bg-primary-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex-shrink-0"
              >
                <Play size={18} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
