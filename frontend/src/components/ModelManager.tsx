import { useState, useEffect } from 'react'
import { Brain, Download, Trash2, RefreshCw, Cpu, HardDrive, Check, Search } from 'lucide-react'

interface ModelInfo {
  name: string
  size?: number
  parameter_size?: string
  format?: string
  families?: string[]
  modified_at?: string
}

interface ModelManagerProps {
  selectedModel: string
  onSelectModel: (model: string) => void
}

const API_BASE = 'http://localhost:8000'

const RECOMMENDED_MODELS = [
  { name: 'qwen3.5:4b', desc: 'Best for 8GB VRAM - coding & chat', size: '~2.5GB', tags: ['coding', 'chat', 'tool-use'] },
  { name: 'llama3.2:3b', desc: 'Fast, lightweight general purpose', size: '~2GB', tags: ['chat', 'fast'] },
  { name: 'deepseek-r1:7b', desc: 'Reasoning powerhouse', size: '~4.5GB', tags: ['reasoning', 'coding'] },
  { name: 'phi4:14b', desc: 'High quality, larger size', size: '~8GB', tags: ['chat', 'quality'] },
  { name: 'codellama:7b', desc: 'Code-focused model', size: '~4GB', tags: ['coding'] },
  { name: 'gemma3:4b', desc: 'Google model, well-rounded', size: '~2.5GB', tags: ['chat', 'coding'] },
]

export default function ModelManager({ selectedModel, onSelectModel }: ModelManagerProps) {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [pullingModel, setPullingModel] = useState<string | null>(null)
  const [pullLog, setPullLog] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  const fetchModels = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/models`)
      const data = await res.json()
      setModels(data.models || [])
    } catch (err) {
      console.error('Failed to fetch models:', err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchModels()
  }, [])

  const pullModel = async (modelName: string) => {
    setPullingModel(modelName)
    setPullLog('')
    try {
      const res = await fetch(`${API_BASE}/api/models/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelName })
      })
      const reader = res.body?.getReader()
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
                setPullingModel(null)
                fetchModels()
                return
              }
              try {
                const parsed = JSON.parse(data)
                setPullLog(prev => prev + (parsed.status || '') + '\n')
              } catch {
                setPullLog(prev => prev + data + '\n')
              }
            }
          }
        }
      }
    } catch (err) {
      console.error('Failed to pull model:', err)
    }
    setPullingModel(null)
    fetchModels()
  }

  const deleteModel = async (modelName: string) => {
    if (!confirm(`Delete model ${modelName}?`)) return
    try {
      await fetch(`${API_BASE}/api/models/${modelName}`, { method: 'DELETE' })
      fetchModels()
    } catch (err) {
      console.error('Failed to delete model:', err)
    }
  }

  const isInstalled = (name: string) => models.some(m => m.name === name)

  const filteredRecommended = RECOMMENDED_MODELS.filter(m =>
    m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.desc.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatSize = (bytes?: number) => {
    if (!bytes) return ''
    const gb = bytes / (1024 * 1024 * 1024)
    return `${gb.toFixed(1)} GB`
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      <header className="flex items-center justify-between px-6 py-3 border-b border-dark-800 bg-dark-900/50">
        <div className="flex items-center gap-3">
          <Brain size={20} className="text-primary-400" />
          <div>
            <h2 className="text-sm font-semibold text-dark-100">Model Manager</h2>
            <p className="text-xs text-dark-500">Install and manage local AI models via Ollama</p>
          </div>
        </div>
        <button
          onClick={fetchModels}
          className="p-2 rounded-lg hover:bg-dark-800 text-dark-500 hover:text-dark-300 transition-all"
          title="Refresh"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </header>

      <div className="flex-1 px-6 py-4 space-y-6 max-w-5xl">
        {/* Installed Models */}
        <section>
          <h3 className="text-sm font-semibold text-dark-200 mb-3 flex items-center gap-2">
            <Cpu size={16} className="text-primary-400" />
            Installed Models ({models.length})
          </h3>
          {models.length === 0 ? (
            <div className="bg-dark-800/50 border border-dark-700/50 rounded-xl p-6 text-center">
              <p className="text-sm text-dark-500">No models installed yet.</p>
              <p className="text-xs text-dark-600 mt-1">Install a model from the recommended list below.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {models.map((model) => (
                <div
                  key={model.name}
                  className={`relative bg-dark-800/50 border rounded-xl p-4 transition-all ${
                    selectedModel === model.name
                      ? 'border-primary-600 bg-primary-600/5'
                      : 'border-dark-700/50 hover:border-dark-600'
                  }`}
                >
                  {selectedModel === model.name && (
                    <span className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary-600 flex items-center justify-center">
                      <Check size={12} className="text-white" />
                    </span>
                  )}
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-dark-100">{model.name}</h4>
                      <div className="flex items-center gap-3 mt-1 text-xs text-dark-500">
                        <span className="flex items-center gap-1">
                          <HardDrive size={12} />
                          {formatSize(model.size)}
                        </span>
                        {model.parameter_size && <span>{model.parameter_size}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <button
                      onClick={() => onSelectModel(model.name)}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        selectedModel === model.name
                          ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30'
                          : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                      }`}
                    >
                      {selectedModel === model.name ? 'Selected' : 'Select'}
                    </button>
                    <button
                      onClick={() => deleteModel(model.name)}
                      className="p-1.5 rounded-lg bg-dark-700 text-dark-500 hover:text-red-400 hover:bg-red-600/10 transition-all"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Recommended Models */}
        <section>
          <h3 className="text-sm font-semibold text-dark-200 mb-3 flex items-center gap-2">
            <Download size={16} className="text-primary-400" />
            Recommended Models
          </h3>

          <div className="relative mb-3">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-600" />
            <input
              type="text"
              placeholder="Search models..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-9 pr-4 py-2 text-sm text-dark-200 placeholder-dark-600 focus:border-primary-600 transition-colors"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredRecommended.map((model) => (
              <div
                key={model.name}
                className="bg-dark-800/50 border border-dark-700/50 rounded-xl p-4 hover:border-dark-600 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-dark-100">{model.name}</h4>
                    <p className="text-xs text-dark-500 mt-0.5">{model.desc}</p>
                    <p className="text-xs text-dark-600 mt-1">{model.size}</p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {model.tags.map((tag) => (
                        <span key={tag} className="px-2 py-0.5 bg-dark-700/50 rounded text-xs text-dark-400">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mt-3">
                  {isInstalled(model.name) ? (
                    <button
                      onClick={() => onSelectModel(model.name)}
                      className="w-full py-1.5 rounded-lg text-xs font-medium bg-primary-600/20 text-primary-400 border border-primary-600/30 transition-all"
                    >
                      Installed - Select
                    </button>
                  ) : (
                    <button
                      onClick={() => pullModel(model.name)}
                      disabled={pullingModel !== null}
                      className="w-full py-1.5 rounded-lg text-xs font-medium bg-primary-600 text-white hover:bg-primary-500 disabled:opacity-50 transition-all"
                    >
                      {pullingModel === model.name ? 'Downloading...' : 'Install'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Pull Log */}
        {pullLog && (
          <div className="bg-dark-800/50 border border-dark-700/50 rounded-xl p-4">
            <h4 className="text-xs font-semibold text-dark-400 mb-2">Download Progress</h4>
            <pre className="text-xs text-dark-500 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">
              {pullLog}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
