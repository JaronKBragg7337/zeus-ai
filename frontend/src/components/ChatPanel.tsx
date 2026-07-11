import { useEffect, useRef, useState } from 'react'
import { BookOpen, Bot, History, MessageSquare, Plus, Send, Square, User, Zap } from 'lucide-react'

interface ChatPanelProps {
  selectedModel: string
}

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

interface ConversationSummary {
  id: string
  title: string
  updated_at: string
  message_count: number
}

interface StoredConversation {
  id: string
  title: string
  messages: Array<{ role: Message['role']; content: string; timestamp: string }>
}

const API_BASE = 'http://localhost:8000'

const welcomeMessage = (): Message => ({
  role: 'system',
  content: 'Welcome to Zeus AI Workbench. I run entirely on your local machine. No data leaves your computer.',
  timestamp: new Date(),
})

const conversationTitle = (items: Message[]) => {
  const firstUser = items.find((item) => item.role === 'user' && item.content.trim())
  const compact = (firstUser?.content || 'New conversation').replace(/\s+/g, ' ').trim()
  return compact.length > 75 ? `${compact.slice(0, 72)}...` : compact
}

export default function ChatPanel({ selectedModel }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([welcomeMessage()])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [useTools, setUseTools] = useState(true)
  const [useRag, setUseRag] = useState(false)
  const [ragCollection, setRagCollection] = useState('default')
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [conversationLabel, setConversationLabel] = useState('New conversation')
  const [historyOpen, setHistoryOpen] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  const refreshConversations = async () => {
    const response = await fetch(`${API_BASE}/api/conversations`)
    if (!response.ok) throw new Error('Could not load conversations')
    const data = await response.json()
    setConversations(data.conversations || [])
  }

  const saveConversation = async (nextMessages: Message[], id = conversationId) => {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: id || undefined,
        title: conversationTitle(nextMessages),
        messages: nextMessages.map((message) => ({
          role: message.role,
          content: message.content,
          timestamp: message.timestamp.toISOString(),
        })),
      }),
    })
    if (!response.ok) throw new Error('Could not save conversation')
    const saved: StoredConversation = await response.json()
    setConversationId(saved.id)
    setConversationLabel(saved.title)
    localStorage.setItem('zeus.activeConversationId', saved.id)
    await refreshConversations()
    return saved.id
  }

  const loadConversation = async (id: string) => {
    const response = await fetch(`${API_BASE}/api/conversations/${id}`)
    if (!response.ok) throw new Error('Could not load conversation')
    const record: StoredConversation = await response.json()
    setMessages(record.messages.map((message) => ({ ...message, timestamp: new Date(message.timestamp) })))
    setConversationId(record.id)
    setConversationLabel(record.title)
    localStorage.setItem('zeus.activeConversationId', record.id)
  }

  const newConversation = () => {
    setMessages([welcomeMessage()])
    setConversationId(null)
    setConversationLabel('New conversation')
    localStorage.removeItem('zeus.activeConversationId')
  }

  useEffect(() => {
    void (async () => {
      try {
        await refreshConversations()
        const activeId = localStorage.getItem('zeus.activeConversationId')
        if (activeId) await loadConversation(activeId)
      } catch {
        // Chat remains usable even if the optional local history store is unavailable.
      }
    })()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [input])

  const handleSubmit = async () => {
    if (!input.trim() || isStreaming) return

    const userMsg: Message = { role: 'user', content: input.trim(), timestamp: new Date() }
    const assistantMsg: Message = { role: 'assistant', content: '', timestamp: new Date() }
    const initialMessages = [...messages, userMsg, assistantMsg]
    setMessages(initialMessages)
    setInput('')
    setIsStreaming(true)
    let assistantContent = ''
    let activeId = conversationId

    try {
      activeId = await saveConversation(initialMessages)
      const chatMessages = [...messages.filter((message) => message.role !== 'system'), userMsg].map((message) => ({
        role: message.role,
        content: message.content,
      }))
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
          rag_collection: ragCollection,
        }),
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`Chat request failed (${response.status})`)

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (reader) {
        let buffer = ''
        const consume = (event: string) => {
          const data = event.split(/\r?\n/).filter((line) => line.startsWith('data: ')).map((line) => line.slice(6)).join('\n')
          if (!data || data === '[DONE]') return
          assistantContent += data
          setMessages((previous) => {
            const last = previous[previous.length - 1]
            return last.role === 'assistant'
              ? [...previous.slice(0, -1), { ...last, content: `${last.content}${data}` }]
              : previous
          })
        }
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const events = buffer.split(/\r?\n\r?\n/)
          buffer = events.pop() || ''
          events.forEach(consume)
        }
        if (buffer.trim()) consume(buffer)
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        assistantContent = `Error: ${(error as Error).message}. Make sure the Zeus backend and Ollama are running.`
        setMessages((previous) => [...previous.slice(0, -1), { ...assistantMsg, content: assistantContent }])
      }
    } finally {
      const finalMessages = [...messages, userMsg, { ...assistantMsg, content: assistantContent || 'Generation stopped.' }]
      try {
        await saveConversation(finalMessages, activeId)
      } catch {
        // The visible chat stays intact if local persistence has a transient failure.
      }
      setIsStreaming(false)
      abortRef.current = null
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void handleSubmit()
    }
  }

  return (
    <div className="flex h-full min-w-0">
      {historyOpen && (
        <aside className="w-64 flex-shrink-0 border-r border-dark-800 bg-dark-900/70 flex flex-col">
          <div className="px-3 py-3 border-b border-dark-800 flex items-center justify-between">
            <span className="text-xs font-semibold text-dark-300">Conversations</span>
            <button onClick={newConversation} title="New conversation" className="p-1.5 text-primary-400 hover:bg-dark-800 rounded-md"><Plus size={16} /></button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.map((thread) => (
              <button key={thread.id} onClick={() => void loadConversation(thread.id)} className={`w-full text-left px-3 py-2 rounded-md transition-colors ${conversationId === thread.id ? 'bg-primary-600/15 text-primary-300' : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200'}`}>
                <span className="block text-xs font-medium truncate">{thread.title}</span>
                <span className="block text-[11px] text-dark-600 mt-1">{thread.message_count} messages</span>
              </button>
            ))}
            {conversations.length === 0 && <p className="px-3 py-4 text-xs text-dark-600">Saved conversations will appear here.</p>}
          </div>
        </aside>
      )}
      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center justify-between px-5 py-3 border-b border-dark-800 bg-dark-900/50">
          <div className="flex items-center gap-3 min-w-0">
            <button onClick={() => setHistoryOpen((open) => !open)} title="Conversation history" className="p-2 text-dark-400 hover:text-dark-100 hover:bg-dark-800 rounded-md"><History size={18} /></button>
            <Bot size={20} className="text-primary-400 flex-shrink-0" />
            <div className="min-w-0"><h2 className="text-sm font-semibold text-dark-100 truncate">{conversationLabel}</h2><p className="text-xs text-dark-500">Model: {selectedModel}</p></div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setUseTools(!useTools)} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium ${useTools ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30' : 'bg-dark-800 text-dark-400 border border-dark-700'}`}><Zap size={14} />Tools</button>
            <button onClick={() => setUseRag(!useRag)} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium ${useRag ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30' : 'bg-dark-800 text-dark-400 border border-dark-700'}`}><BookOpen size={14} />RAG</button>
            {useRag && <select value={ragCollection} onChange={(event) => setRagCollection(event.target.value)} className="bg-dark-800 border border-dark-700 rounded-md text-xs px-2 py-1.5 text-dark-300"><option value="default">default</option></select>}
          </div>
        </header>
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.map((message, index) => (
            <div key={`${message.timestamp.getTime()}-${index}`} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
              {message.role === 'assistant' && <div className="w-8 h-8 rounded-md bg-primary-600/20 flex items-center justify-center flex-shrink-0 mt-1"><Bot size={16} className="text-primary-400" /></div>}
              <div className={`max-w-[80%] rounded-lg px-4 py-3 ${message.role === 'user' ? 'bg-primary-600 text-white' : message.role === 'system' ? 'bg-dark-800/50 border border-dark-700/50 text-dark-400 text-xs' : 'bg-dark-800 border border-dark-700/50 text-dark-200'}`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>
              {message.role === 'user' && <div className="w-8 h-8 rounded-md bg-dark-700 flex items-center justify-center flex-shrink-0 mt-1"><User size={16} className="text-dark-300" /></div>}
            </div>
          ))}
          {isStreaming && !messages[messages.length - 1]?.content && <div className="flex gap-3"><div className="w-8 h-8 rounded-md bg-primary-600/20 flex items-center justify-center"><Bot size={16} className="text-primary-400" /></div><div className="bg-dark-800 border border-dark-700/50 rounded-lg px-4 py-3 text-sm text-dark-500">Thinking...</div></div>}
          <div ref={messagesEndRef} />
        </div>
        <div className="border-t border-dark-800 bg-dark-900/50 px-4 py-3">
          <div className="flex gap-2">
            <button title="New conversation" onClick={newConversation} className="p-2.5 rounded-md text-dark-400 hover:bg-dark-800 hover:text-dark-100"><MessageSquare size={18} /></button>
            <textarea ref={textareaRef} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} placeholder="Ask anything... (Shift+Enter for new line)" className="flex-1 bg-dark-800 border border-dark-700 rounded-md px-4 py-3 text-sm text-dark-200 placeholder-dark-500 resize-none focus:border-primary-600" rows={1} disabled={isStreaming} />
            {isStreaming ? <button onClick={() => abortRef.current?.abort()} className="p-2.5 rounded-md bg-red-600/20 text-red-400"><Square size={18} /></button> : <button onClick={() => void handleSubmit()} disabled={!input.trim()} className="p-2.5 rounded-md bg-primary-600 text-white hover:bg-primary-500 disabled:opacity-40"><Send size={18} /></button>}
          </div>
        </div>
      </div>
    </div>
  )
}
