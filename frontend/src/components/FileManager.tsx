import { useState, useEffect } from 'react'
import { Folder, File, ChevronRight, ChevronLeft, Home, RefreshCw, Eye, Save, X } from 'lucide-react'

interface FileEntry {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
}

const API_BASE = 'http://localhost:8000'

export default function FileManager() {
  const [currentPath, setCurrentPath] = useState('.')
  const [files, setFiles] = useState<FileEntry[]>([])
  const [history, setHistory] = useState<string[]>((['.']))
  const [historyIndex, setHistoryIndex] = useState(0)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchFiles = async (path: string) => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/files/list`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      })
      const data = await res.json()
      if (data.files) {
        setFiles(data.files)
        setCurrentPath(data.path)
      }
    } catch (err) {
      console.error('Failed to list files:', err)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchFiles(currentPath)
  }, [])

  const navigateTo = (path: string) => {
    const newHistory = history.slice(0, historyIndex + 1)
    newHistory.push(path)
    setHistory(newHistory)
    setHistoryIndex(newHistory.length - 1)
    fetchFiles(path)
  }

  const goBack = () => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1
      setHistoryIndex(newIndex)
      fetchFiles(history[newIndex])
    }
  }

  const goForward = () => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1
      setHistoryIndex(newIndex)
      fetchFiles(history[newIndex])
    }
  }

  const goHome = () => {
    navigateTo('.')
  }

  const openFile = async (path: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/files/read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      })
      const data = await res.json()
      if (data.content) {
        setSelectedFile(path)
        setFileContent(data.content)
        setEditContent(data.content)
        setIsEditing(false)
      }
    } catch (err) {
      console.error('Failed to read file:', err)
    }
  }

  const saveFile = async () => {
    if (!selectedFile) return
    try {
      const res = await fetch(`${API_BASE}/api/files/write`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: selectedFile, content: editContent })
      })
      const data = await res.json()
      if (data.success) {
        setFileContent(editContent)
        setIsEditing(false)
      }
    } catch (err) {
      console.error('Failed to write file:', err)
    }
  }

  const formatSize = (bytes?: number) => {
    if (bytes === undefined) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="flex h-full">
      {/* File List */}
      <div className={`${selectedFile ? 'w-1/2' : 'w-full'} flex flex-col border-r border-dark-800`}>
        <header className="flex items-center gap-2 px-4 py-3 border-b border-dark-800 bg-dark-900/50">
          <button onClick={goBack} className="p-1.5 rounded-lg hover:bg-dark-800 text-dark-500 hover:text-dark-300 transition-all">
            <ChevronLeft size={16} />
          </button>
          <button onClick={goForward} className="p-1.5 rounded-lg hover:bg-dark-800 text-dark-500 hover:text-dark-300 transition-all">
            <ChevronRight size={16} />
          </button>
          <button onClick={goHome} className="p-1.5 rounded-lg hover:bg-dark-800 text-dark-500 hover:text-dark-300 transition-all">
            <Home size={16} />
          </button>
          <div className="flex-1 bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-xs text-dark-300 font-mono truncate">
            {currentPath}
          </div>
          <button onClick={() => fetchFiles(currentPath)} className="p-1.5 rounded-lg hover:bg-dark-800 text-dark-500 hover:text-dark-300 transition-all">
            <RefreshCw size={16} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto">
          {/* Header row */}
          <div className="flex items-center px-4 py-2 text-xs font-medium text-dark-500 border-b border-dark-800/50">
            <span className="flex-1">Name</span>
            <span className="w-24 text-right">Size</span>
          </div>

          {/* Parent directory */}
          {currentPath !== '.' && (
            <button
              onClick={() => navigateTo(currentPath.split('/').slice(0, -1).join('/') || '.')}
              className="flex items-center w-full px-4 py-2 hover:bg-dark-800/50 transition-colors text-left"
            >
              <Folder size={16} className="text-dark-600 mr-2" />
              <span className="text-sm text-dark-400">..</span>
            </button>
          )}

          {/* Files */}
          {files.map((file) => (
            <button
              key={file.path}
              onClick={() => file.type === 'directory' ? navigateTo(file.path) : openFile(file.path)}
              className={`flex items-center w-full px-4 py-2 hover:bg-dark-800/50 transition-colors text-left ${
                selectedFile === file.path ? 'bg-primary-600/10 border-l-2 border-primary-600' : ''
              }`}
            >
              {file.type === 'directory' ? (
                <Folder size={16} className="text-amber-500 mr-2 flex-shrink-0" />
              ) : (
                <File size={16} className="text-primary-400 mr-2 flex-shrink-0" />
              )}
              <span className="flex-1 text-sm text-dark-200 truncate">{file.name}</span>
              <span className="w-24 text-right text-xs text-dark-500">{formatSize(file.size)}</span>
            </button>
          ))}

          {files.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center py-12 text-dark-600">
              <Folder size={32} className="mb-2" />
              <p className="text-sm">Empty folder</p>
            </div>
          )}
        </div>
      </div>

      {/* File Viewer */}
      {selectedFile && (
        <div className="w-1/2 flex flex-col bg-dark-900/30">
          <div className="flex items-center justify-between px-4 py-3 border-b border-dark-800 bg-dark-900/50">
            <div className="flex items-center gap-2">
              <Eye size={14} className="text-primary-400" />
              <span className="text-xs font-mono text-dark-300 truncate max-w-xs">{selectedFile}</span>
            </div>
            <div className="flex items-center gap-2">
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-3 py-1.5 rounded-lg bg-dark-800 text-xs text-dark-300 hover:text-dark-100 border border-dark-700 transition-all"
                >
                  Edit
                </button>
              ) : (
                <>
                  <button
                    onClick={saveFile}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-600 text-xs text-white hover:bg-primary-500 transition-all"
                  >
                    <Save size={12} />
                    Save
                  </button>
                  <button
                    onClick={() => { setIsEditing(false); setEditContent(fileContent) }}
                    className="px-3 py-1.5 rounded-lg bg-dark-800 text-xs text-dark-400 hover:text-dark-200 border border-dark-700 transition-all"
                  >
                    Cancel
                  </button>
                </>
              )}
              <button
                onClick={() => setSelectedFile(null)}
                className="p-1.5 rounded-lg hover:bg-dark-800 text-dark-500 hover:text-dark-300 transition-all"
              >
                <X size={16} />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {isEditing ? (
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-full bg-dark-950 border border-dark-700 rounded-lg p-4 text-sm font-mono text-dark-200 resize-none focus:border-primary-600 transition-colors"
                spellCheck={false}
              />
            ) : (
              <pre className="text-sm font-mono text-dark-300 whitespace-pre-wrap leading-relaxed">
                {fileContent}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
