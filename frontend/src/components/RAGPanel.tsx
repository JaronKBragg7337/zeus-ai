import { useState, useRef, useEffect } from 'react'
import { Upload, Database, Trash2, FileText, Search, Plus, X, Check, AlertCircle } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

export default function RAGPanel() {
  const [collections, setCollections] = useState<string[]>([])
  const [activeCollection, setActiveCollection] = useState('default')
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [queryResults, setQueryResults] = useState<any[]>([])
  const [querying, setQuerying] = useState(false)
  const [newCollectionName, setNewCollectionName] = useState('')
  const [showNewCollection, setShowNewCollection] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchCollections = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/rag/collections`)
      const data = await res.json()
      setCollections(data.collections || [])
    } catch (err) {
      console.error('Failed to fetch collections:', err)
    }
  }

  useEffect(() => {
    fetchCollections()
  }, [])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setUploadResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('collection', activeCollection)

    try {
      const res = await fetch(`${API_BASE}/api/rag/upload`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.error) {
        setUploadResult(`Error: ${data.error}`)
      } else {
        setUploadResult(`Success! Processed ${data.chunks || 0} chunks from "${data.filename}"`)
        fetchCollections()
      }
    } catch (err) {
      setUploadResult(`Error: ${(err as Error).message}`)
    }
    setUploading(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleQuery = async () => {
    if (!query.trim()) return
    setQuerying(true)
    try {
      const res = await fetch(`${API_BASE}/api/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: query,
          collection: activeCollection,
          top_k: 5
        })
      })
      const data = await res.json()
      setQueryResults(data.documents || [])
    } catch (err) {
      console.error('Query failed:', err)
    }
    setQuerying(false)
  }

  const deleteCollection = async (name: string) => {
    if (!confirm(`Delete collection "${name}"? All documents will be removed.`)) return
    try {
      await fetch(`${API_BASE}/api/rag/collections/${name}`, { method: 'DELETE' })
      fetchCollections()
      if (activeCollection === name) setActiveCollection('default')
    } catch (err) {
      console.error('Failed to delete collection:', err)
    }
  }

  const createCollection = () => {
    if (!newCollectionName.trim()) return
    setActiveCollection(newCollectionName.trim())
    setCollections(prev => [...prev, newCollectionName.trim()])
    setNewCollectionName('')
    setShowNewCollection(false)
  }

  return (
    <div className="flex h-full">
      {/* Sidebar - Collections */}
      <div className="w-64 border-r border-dark-800 bg-dark-900/30 flex flex-col">
        <div className="px-4 py-3 border-b border-dark-800">
          <h3 className="text-sm font-semibold text-dark-200 flex items-center gap-2">
            <Database size={16} className="text-primary-400" />
            Collections
          </h3>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {collections.map((name) => (
            <div
              key={name}
              className={`flex items-center justify-between px-4 py-2 cursor-pointer transition-all ${
                activeCollection === name ? 'bg-primary-600/10 border-r-2 border-primary-600' : 'hover:bg-dark-800/50'
              }`}
              onClick={() => setActiveCollection(name)}
            >
              <span className={`text-sm ${activeCollection === name ? 'text-primary-400' : 'text-dark-400'}`}>
                {name}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); deleteCollection(name) }}
                className="p-1 rounded hover:bg-dark-700 text-dark-600 hover:text-red-400 transition-all opacity-0 group-hover:opacity-100"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}

          {showNewCollection ? (
            <div className="px-4 py-2">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  placeholder="Collection name"
                  className="flex-1 bg-dark-800 border border-dark-700 rounded-lg px-2 py-1 text-xs text-dark-200 placeholder-dark-600 focus:border-primary-600"
                  autoFocus
                  onKeyDown={(e) => { if (e.key === 'Enter') createCollection() }}
                />
                <button onClick={createCollection} className="p-1 rounded hover:bg-dark-700 text-primary-400">
                  <Check size={14} />
                </button>
                <button onClick={() => setShowNewCollection(false)} className="p-1 rounded hover:bg-dark-700 text-dark-500">
                  <X size={14} />
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowNewCollection(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm text-dark-500 hover:text-dark-300 transition-all w-full"
            >
              <Plus size={14} />
              New Collection
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        <header className="px-6 py-3 border-b border-dark-800 bg-dark-900/50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-dark-100">Document Manager</h2>
              <p className="text-xs text-dark-500">Collection: {activeCollection}</p>
            </div>
          </div>
        </header>

        <div className="flex-1 px-6 py-6 space-y-6 max-w-3xl">
          {/* Upload Section */}
          <section className="bg-dark-800/30 border border-dark-700/50 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-dark-200 mb-3 flex items-center gap-2">
              <Upload size={16} className="text-primary-400" />
              Upload Document
            </h3>
            <p className="text-xs text-dark-500 mb-4">
              Upload PDF, DOCX, TXT, MD, or code files. The AI will index them for question-answering.
            </p>
            <div
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                uploading
                  ? 'border-primary-600/50 bg-primary-600/5'
                  : 'border-dark-700 hover:border-dark-600 hover:bg-dark-800/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                accept=".pdf,.docx,.txt,.md,.py,.js,.ts,.json,.html,.css,.csv"
              />
              {uploading ? (
                <div className="flex flex-col items-center">
                  <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mb-2" />
                  <p className="text-sm text-primary-400">Processing document...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <FileText size={32} className="text-dark-600 mb-2" />
                  <p className="text-sm text-dark-400">Click to upload or drag a file here</p>
                  <p className="text-xs text-dark-600 mt-1">PDF, DOCX, TXT, MD, Code files</p>
                </div>
              )}
            </div>
            {uploadResult && (
              <div className={`mt-3 px-3 py-2 rounded-lg text-xs flex items-center gap-2 ${
                uploadResult.startsWith('Error')
                  ? 'bg-red-600/10 text-red-400 border border-red-600/20'
                  : 'bg-emerald-600/10 text-emerald-400 border border-emerald-600/20'
              }`}>
                {uploadResult.startsWith('Error') ? <AlertCircle size={14} /> : <Check size={14} />}
                {uploadResult}
              </div>
            )}
          </section>

          {/* Query Section */}
          <section className="bg-dark-800/30 border border-dark-700/50 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-dark-200 mb-3 flex items-center gap-2">
              <Search size={16} className="text-primary-400" />
              Test Query
            </h3>
            <p className="text-xs text-dark-500 mb-4">
              Ask a question about your uploaded documents to test the RAG system.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleQuery() }}
                placeholder="Ask about your documents..."
                className="flex-1 bg-dark-800 border border-dark-700 rounded-lg px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 focus:border-primary-600 transition-colors"
              />
              <button
                onClick={handleQuery}
                disabled={querying || !query.trim()}
                className="px-4 rounded-lg bg-primary-600 text-white hover:bg-primary-500 disabled:opacity-40 transition-all"
              >
                {querying ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Search size={18} />
                )}
              </button>
            </div>

            {/* Results */}
            {queryResults.length > 0 && (
              <div className="mt-4 space-y-3">
                <h4 className="text-xs font-semibold text-dark-400">Retrieved passages:</h4>
                {queryResults.map((doc, i) => (
                  <div key={i} className="bg-dark-800/50 border border-dark-700/30 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-primary-400">{doc.source}</span>
                      <span className="text-xs text-dark-600">Relevance: {(1 - doc.relevance).toFixed(3)}</span>
                    </div>
                    <p className="text-xs text-dark-400 leading-relaxed">{doc.content}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
