"""Zeus AI Workbench - FastAPI Backend"""
import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import (
    ChatRequest, ChatMessage, ModelPullRequest,
    ProjectPath, FileOperation, AgentTask, ToolCall, RAGQuery
)
from ollama_client import ollama
from tools import get_tool_definitions, execute_tool, _resolve_allowed_path
from agent import run_agent_task
from rag_engine import rag_engine
from config import UPLOAD_DIR, format_allowed_roots, is_full_computer_access_enabled, get_command_risk_policy
from audit_log import read_recent_actions
from runtime_control import clear_stop, request_stop, status as runtime_status

app = FastAPI(
    title="Zeus AI Workbench",
    description="100% Local AI Agent with Tool Use and RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR.mkdir(exist_ok=True)

# ─── Health ───
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "zeus-ai",
        "allowed_roots": format_allowed_roots(),
        "full_computer_access": is_full_computer_access_enabled(),
        "command_risk_policy": get_command_risk_policy(),
        "runtime": runtime_status(),
    }

@app.get("/api/audit/actions")
async def audit_actions(limit: int = 100):
    return {"actions": read_recent_actions(limit)}

@app.post("/api/control/kill")
async def kill(reason: str = "manual"):
    return request_stop(reason)

@app.post("/api/control/resume")
async def resume():
    return clear_stop()

@app.get("/api/control/status")
async def control_status():
    return runtime_status()

# ─── Models ───
@app.get("/api/models")
async def list_models():
    """List available Ollama models."""
    try:
        models = await ollama.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(500, f"Ollama connection failed: {e}")

@app.post("/api/models/pull")
async def pull_model(req: ModelPullRequest):
    """Pull a model from Ollama registry."""
    async def stream_pull():
        async for update in ollama.pull_model(req.model_name):
            yield f"data: {update}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(stream_pull(), media_type="text/event-stream")

@app.delete("/api/models/{model_name}")
async def delete_model(model_name: str):
    success = await ollama.delete_model(model_name)
    return {"success": success}

# ─── Chat ───
@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Stream chat completions."""
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    # Add RAG context if requested
    if req.use_rag and req.rag_collection:
        last_msg = messages[-1]["content"] if messages else ""
        rag_result = await rag_engine.query(last_msg, req.rag_collection)
        if "context" in rag_result and rag_result["context"]:
            context_msg = (
                f"Use the following context to answer:\n\n{rag_result['context']}\n\n"
                f"Question: {last_msg}"
            )
            messages[-1]["content"] = context_msg

    tools = get_tool_definitions() if req.use_tools else None

    async def stream_response():
        full_response = ""
        async for chunk in ollama.chat(messages, req.model, req.stream, req.temperature, tools):
            full_response += chunk
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")

# ─── Agent ───
@app.post("/api/agent")
async def agent_task(req: AgentTask):
    """Run an agent task with tool use."""
    async def stream_agent():
        async for update in run_agent_task(req.task, req.model, req.project_path, req.max_steps):
            import json
            yield f"data: {json.dumps(update)}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(stream_agent(), media_type="text/event-stream")

# ─── Tools ───
@app.get("/api/tools")
async def list_tools():
    """List available tools."""
    return {"tools": get_tool_definitions()}

@app.post("/api/tools/execute")
async def execute_tool_endpoint(req: ToolCall):
    """Execute a single tool."""
    result = execute_tool(req.name, req.parameters)
    return result

# ─── File Operations ───
@app.post("/api/files/list")
async def list_files(req: ProjectPath):
    result = execute_tool("list_files", {"path": req.path, "recursive": False})
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result

@app.post("/api/files/read")
async def read_file(req: FileOperation):
    result = execute_tool("read_file", {"path": req.path})
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result

@app.post("/api/files/write")
async def write_file(req: FileOperation):
    if not req.content:
        raise HTTPException(400, "Content required")
    result = execute_tool("write_file", {"path": req.path, "content": req.content})
    return result

@app.get("/api/files/download")
async def download_file(path: str):
    try:
        p = _resolve_allowed_path(path)
    except ValueError as e:
        raise HTTPException(403, str(e))
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "File not found")
    from fastapi.responses import FileResponse
    return FileResponse(p, filename=p.name)

# ─── RAG / Documents ───
@app.post("/api/rag/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default")
):
    """Upload a document for RAG."""
    safe_name = Path(file.filename or "upload.txt").name
    file_path = UPLOAD_DIR / safe_name
    content = await file.read()
    file_path.write_bytes(content)

    # Extract text based on file type
    text = ""
    try:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                for page in reader.pages:
                    text += page.extract_text() or ""
            except ImportError:
                return {"error": "pypdf not installed. pip install pypdf"}
        elif suffix in [".docx", ".doc"]:
            try:
                import docx
                doc = docx.Document(str(file_path))
                text = "\n".join([p.text for p in doc.paragraphs])
            except ImportError:
                return {"error": "python-docx not installed"}
        elif suffix in [".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html", ".css", ".xml", ".csv", ".log", ".ini", ".cfg", ".sh", ".bat"]:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        else:
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return {"error": f"Cannot extract text from {suffix} files"}
    except Exception as e:
        return {"error": f"Text extraction failed: {e}"}

    if not text.strip():
        return {"error": "No text content extracted from file"}

    result = await rag_engine.ingest_document(text, safe_name, collection)
    result["filename"] = safe_name
    return result

@app.get("/api/rag/collections")
async def list_collections():
    collections = await rag_engine.list_collections()
    return {"collections": collections}

@app.get("/api/rag/collections/{name}")
async def collection_info(name: str):
    return await rag_engine.collection_info(name)

@app.delete("/api/rag/collections/{name}")
async def delete_collection(name: str):
    success = await rag_engine.delete_collection(name)
    return {"success": success}

@app.post("/api/rag/query")
async def query_rag(req: RAGQuery):
    return await rag_engine.query(req.question, req.collection, req.top_k)

# ─── Startup ───
@app.on_event("startup")
async def startup():
    await rag_engine.initialize()
    print("Zeus AI Workbench started!")
    if os.getenv("ZEUSAI_DESKTOP") == "1":
        print("Desktop sidecar backend is running.")
    else:
        print("Open http://localhost:8000 in your browser after starting the frontend.")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("ZEUSAI_BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("ZEUSAI_BACKEND_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
