import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import FileManager from './components/FileManager'
import ModelManager from './components/ModelManager'
import RAGPanel from './components/RAGPanel'
import AgentPanel from './components/AgentPanel'

export type PanelType = 'chat' | 'agent' | 'files' | 'models' | 'rag'

function App() {
  const [activePanel, setActivePanel] = useState<PanelType>('chat')
  const [selectedModel, setSelectedModel] = useState('qwen3.5:4b')

  const renderPanel = () => {
    switch (activePanel) {
      case 'chat':
        return <ChatPanel selectedModel={selectedModel} />
      case 'agent':
        return <AgentPanel selectedModel={selectedModel} />
      case 'files':
        return <FileManager />
      case 'models':
        return <ModelManager selectedModel={selectedModel} onSelectModel={setSelectedModel} />
      case 'rag':
        return <RAGPanel />
      default:
        return <ChatPanel selectedModel={selectedModel} />
    }
  }

  return (
    <div className="flex h-screen w-screen bg-dark-950 text-dark-200 overflow-hidden">
      <Sidebar activePanel={activePanel} onPanelChange={setActivePanel} />
      <main className="flex-1 overflow-hidden">
        {renderPanel()}
      </main>
    </div>
  )
}

export default App
