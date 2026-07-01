# 🤖 OmniLocal AI Workbench

**Your Private, Local AI Command Center — 100% Free, 100% Offline, 100% Yours.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-ff6f00?logo=ollama)](https://ollama.ai)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)

OmniLocal is a fully self-hosted AI workbench that runs entirely on your machine. Chat with AI models, let agents execute tasks on your computer, query your documents, and manage your local models — all without sending a single byte to the cloud.

---

## 🔥 What Makes This Different

| Feature | OmniLocal | ChatGPT | Claude | Cursor |
|---------|-----------|---------|--------|--------|
| **100% Local** | ✅ No internet needed | ❌ Cloud-only | ❌ Cloud-only | ❌ Cloud sync |
| **Zero API Costs** | ✅ Completely free | 💰 $20/mo | 💰 $20/mo | 💰 $20/mo |
| **Agent Tools** | ✅ Files, shell, search | ❌ | ❌ Code only | ❌ Limited |
| **Document RAG** | ✅ Local embeddings | ✅ Cloud stored | ✅ Cloud stored | ❌ |
| **Code Editor** | ✅ Built-in file editor | ❌ | ❌ | ✅ Full IDE |
| **Model Manager** | ✅ Install any Ollama model | ❌ GPT only | ❌ Claude only | ❌ Limited |
| **Privacy** | ✅ Data never leaves PC | ❌ Server processed | ❌ Server processed | ⚠️ Synced |

---

## ✨ Features

### 💬 AI Chat
- Multi-model chat interface — switch between any installed Ollama model
- Streaming responses with real-time typing indicator
- Toggle **Tool Use** to let AI read files, run commands, search your codebase
- Toggle **RAG** to ask questions about your uploaded documents

### 🔧 AI Agent Mode
- Multi-step autonomous task execution
- Built-in tools: file read/write, directory listing, shell commands, file search, project structure analysis, calculations
- The AI reasons through tasks step-by-step, using tools as needed
- Perfect for: code analysis, refactoring, documentation generation, system administration

### 📁 File Manager
- Browse your filesystem with a clean tree view
- Read and edit files directly in the browser
- Syntax-friendly display for code files
- Navigate directories with breadcrumb-style path

### 📚 Document RAG (Retrieval Augmented Generation)
- Upload PDF, DOCX, TXT, MD, and code files
- Local sentence-transformer embeddings (no API calls)
- Ask questions about your documents and get grounded answers
- Organize documents into named collections

### 🧠 Model Manager
- View installed Ollama models with size and parameter info
- Install new models with one click (curated recommendations for your hardware)
- Delete models to free up space
- Hardware-aware recommendations for 8GB VRAM systems

---

## 🚀 Quick Start

### Prerequisites

1. **[Ollama](https://ollama.ai)** — Install and make sure it's running
2. **[Python 3.10+](https://python.org)** — Required for the backend
3. **[Node.js 18+](https://nodejs.org)** — Required for the frontend

### Option 1: Windows Batch Script (Easiest)

```bash
# Double-click or run in Command Prompt:
start.bat
```

### Option 2: PowerShell Script

```powershell
# Run in PowerShell:
.\start.ps1
```

### Option 3: Manual Start

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2 — Frontend (new terminal)
cd frontend
npm install --no-bin-links
npm run dev

# Open http://localhost:3000 in your browser
```

---

## 📋 First Time Setup

### 1. Install Ollama Models

OmniLocal doesn't come with AI models — you choose what to install. For your **RTX 4060 8GB**:

```bash
# Best all-rounder (recommended)
ollama pull qwen3.5:4b

# Fast and lightweight
ollama pull llama3.2:3b

# Strong reasoning
ollama pull deepseek-r1:7b

# Code-focused
ollama pull codellama:7b
```

### 2. Verify Everything Works

Open http://localhost:3000 and:
1. Go to **Models** tab — you should see your installed models
2. Click **Select** on your preferred model
3. Go to **Chat** tab and send a message
4. Try asking: "What can you help me with?"

---

## 🛠️ System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU VRAM** | 4GB | 8GB+ |
| **RAM** | 8GB | 16GB+ |
| **Storage** | 10GB free | 50GB+ for models |
| **OS** | Windows 10/11, Linux, macOS | Windows 11 |
| **CPU** | Any modern CPU | 6+ cores |

---

## 📁 Project Structure

```
omnilocal-ai/
├── backend/              # Python FastAPI backend
│   ├── main.py           # API server
│   ├── ollama_client.py  # Ollama integration
│   ├── tools.py          # Agent tools (file, shell, search)
│   ├── agent.py          # Multi-step agent logic
│   ├── rag_engine.py     # Local RAG with embeddings
│   └── requirements.txt  # Python dependencies
├── frontend/             # React + Vite frontend
│   ├── src/
│   │   ├── components/   # UI panels
│   │   ├── App.tsx       # Main app
│   │   └── index.css     # Styles
│   └── package.json
├── start.bat             # Windows startup
├── start.ps1             # PowerShell startup
└── README.md
```

---

## 🔒 Privacy & Security

- **No external API calls** — Everything runs on your machine
- **No data collection** — Zero telemetry, zero tracking
- **No cloud dependencies** — Works fully offline
- **Your models, your data** — Models downloaded to your machine only
- **Local embeddings** — Document vectors computed locally, never uploaded

---

## 🧩 Tech Stack

**Backend:**
- FastAPI — High-performance Python API
- Ollama — Local LLM inference
- ChromaDB — Local vector database
- Sentence-Transformers — CPU-based embeddings
- PyPDF / python-docx — Document parsing

**Frontend:**
- React 19 + TypeScript
- Vite — Fast builds
- Tailwind CSS — Styling
- Lucide React — Icons

---

## 🌟 Why I Built This

The AI landscape is dominated by cloud services that charge subscriptions and process your data on their servers. I believe everyone deserves access to powerful AI tools that respect their privacy and don't require ongoing payments.

OmniLocal is designed to be:
- **Accessible** — Works on consumer hardware (tested on RTX 4060 8GB)
- **Useful** — Real tools for real work, not just chat
- **Transparent** — Fully open source, no black boxes
- **Yours** — You own it, you control it, it works offline

---

## 🚧 Roadmap

- [x] Multi-model chat with streaming
- [x] AI Agent with tool use (files, shell, search)
- [x] Local RAG for document Q&A
- [x] File browser and editor
- [x] Model manager
- [ ] Code syntax highlighting in chat
- [ ] Conversation history and persistence
- [ ] Multi-modal support (images, audio)
- [ ] Plugin system for custom tools
- [ ] Desktop app packaging (Tauri/Electron)

---

## 🤝 Contributing

This project is open source and contributions are welcome! Whether it's bug fixes, new features, or documentation improvements — all help is appreciated.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License — free for personal and commercial use.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) — Making local LLMs accessible
- [Qwen](https://github.com/QwenLM/Qwen) — Excellent small models for consumer hardware
- [Meta Llama](https://llama.meta.com) — Open foundation models
- [ChromaDB](https://trychroma.com) — Open-source vector database

---

**Built with ❤️ for the local AI community.**

*Star this repo if you find it useful — it helps others discover it!*
