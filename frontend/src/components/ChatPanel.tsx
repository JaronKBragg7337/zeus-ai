import { useState, useRef, useEffect } from 'react'
import { Send, Square, Paperclip, Bot, User, Zap, BookOpen } from 'lucide-react'

interface ChatPanelProps {
  selectedModel: string
}

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

const API_BASE = 'http://localhost:8000'

export default function ChatPanel({ selectedModel }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'system', content: 'Welcome to Zeus AI Workbench. I run entirely on your local machine. No data leaves your computer.', timestamp: new Date() }
  ])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [useTools, setUseTools] = useState(false)
  const [useRag, setUseRag] = useState(false)
  const [ragCollection, setRagCollection] = useState('default')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px'
    }
  }, [input])

  const handleSubmit = async () => {
    if (!input.trim() || isStreaming) return

    const userMsg: Message = { role: 'user', content: input.trim(), timestamp: new Date() }
    const assistantMsg: Message = { role: 'assistant', content: '', timestamp: new Date() }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setInput('')
    setIsStreaming(true)

    const chatMessages = [...messages.filter(m => m.role !== 'system'), userMsg].map(m => ({
      role: m.role,
      content: m.content
    }))

    try {
      const controller = new AbortController()
      abortRef.current = controller

      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: chatMessages,
          model: selectedModel,
          stream: true,
          temperature: 0.7,
          use_tools: useTools,
          use_rag: useRag,
          rag_collection: ragCollection
        }),
        signal: controller.signal
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
              if (data === '[DONE]') break
              setMessages(prev => {
                const last = prev[prev.length - 1]
                if (last.role === 'assistant') {
                  return [...prev.slice(0, -1), { ...last, content: last.content + data }]
                }
                return prev
              })
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setMessages(prev => [...prev, {
          role: 'system',
          content: `Error: ${(err as Error).message}. Make sure the backend is running on port 8000 and Ollama is running.`,
          timestamp: new Date()
        }])
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const stopGeneration = () => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-dark-800 bg-dark-900/50">
        <div className="flex items-center gap-3">
          <Bot size={20} className="text-primary-400" />
          <div>
            <h2 className="text-sm font-semibold text-dark-100">AI Chat</h2>
            <p className="text-xs text-dark-500">Model: {selectedModel}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Tool toggle */}
          <button
            onClick={() => setUseTools(!useTools)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              useTools
                ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30'
                : 'bg-dark-800 text-dark-400 border border-dark-700 hover:text-dark-300'
            }`}
          >
            <Zap size={14} />
            Tools
          </button>
          {/* RAG toggle */}
          <button
            onClick={() => setUseRag(!useRag)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              useRag
                ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30'
                : 'bg-dark-800 text-dark-400 border border-dark-700 hover:text-dark-300'
            }`}
          >
            <BookOpen size={14} />
            RAG
          </button>
          {useRag && (
            <select
              value={ragCollection}
              onChange={(e) => setRagCollection(e.target.value)}
              className="bg-dark-800 border border-dark-700 rounded-lg text-xs px-2 py-1.5 text-dark-300 focus:border-primary-600"
            >
              <option value="default">default</option>
            </select>
          )}
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-primary-600/20 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot size={16} className="text-primary-400" />
              </div>
            )}
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-primary-600 text-white rounded-br-md'
                : msg.role === 'system'
                ? 'bg-dark-800/50 border border-dark-700/50 text-dark-400 text-xs'
                : 'bg-dark-800 border border-dark-700/50 text-dark-200 rounded-bl-md'
            }`}>
              {msg.role === 'assistant' ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed bg-transparent p-0">
                    {msg.content}
                  </pre>
                </div>
              ) : (
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-dark-700 flex items-center justify-center flex-shrink-0 mt-1">
                <User size={16} className="text-dark-300" />
              </div>
            )}
          </div>
        ))}

        {isStreaming && messages[messages.length - 1]?.content === '' && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-lg bg-primary-600/20 flex items-center justify-center flex-shrink-0">
              <Bot size={16} className="text-primary-400" />
            </div>
            <div className="bg-dark-800 border border-dark-700/50 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
                <span className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
                <span className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-dark-800 bg-dark-900/50 px-4 py-3">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          <button className="p-2.5 rounded-xl text-dark-500 hover:text-dark-300 hover:bg-dark-800 transition-all flex-shrink-0">
            <Paperclip size={18} />
          </button>
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything... (Shift+Enter for new line)"
              className="w-full bg-dark-800 border border-dark-700 rounded-xl px-4 py-3 text-sm text-dark-200 placeholder-dark-500 resize-none focus:border-primary-600 transition-colors"
              rows={1}
              disabled={isStreaming}
            />
          </div>
          {isStreaming ? (
            <button
              onClick={stopGeneration}
              className="p-2.5 rounded-xl bg-red-600/20 text-red-400 hover:bg-red-600/30 transition-all flex-shrink-0"
            >
              <Square size={18} />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="p-2.5 rounded-xl bg-primary-600 text-white hover:bg-primary-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex-shrink-0"
            >
              <Send size={18} />
            </button>
          )}
        </div>
        <p className="text-center text-xs text-dark-600 mt-2">
          Zeus AI runs 100% locally. Your data never leaves this machine.
        </p>
      </div>
    </div>
  )
}
