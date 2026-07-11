"""Pydantic models for the Zeus AI Workbench API."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "qwen3.5:4b"
    stream: bool = True
    temperature: float = 0.7
    use_tools: bool = False
    use_rag: bool = False
    rag_collection: Optional[str] = None
    use_memory: bool = True


class ConversationMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: str


class ConversationSaveRequest(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    messages: List[ConversationMessage]


class MemoryUpsert(BaseModel):
    id: Optional[str] = None
    content: str
    category: str = "note"
    source: str = "manual"
    tags: List[str] = []


class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    result: str
    error: Optional[str] = None


class DocumentUpload(BaseModel):
    collection_name: str = "default"


class ModelInfo(BaseModel):
    name: str
    size: Optional[int] = None
    parameter_size: Optional[str] = None
    format: Optional[str] = None
    families: Optional[List[str]] = None


class ModelPullRequest(BaseModel):
    model_name: str


class ProjectPath(BaseModel):
    path: str


class FileOperation(BaseModel):
    path: str
    content: Optional[str] = None


class AgentTask(BaseModel):
    task: str
    model: str = "qwen3.5:4b"
    project_path: Optional[str] = None
    max_steps: int = 10


class RAGQuery(BaseModel):
    question: str
    collection: str = "default"
    top_k: int = 5


class TrainingCorrection(BaseModel):
    original: str
    correction: str
    context: Optional[str] = None


class TrainingReview(BaseModel):
    candidate_id: str
    approved: bool
    reviewer: str = "user"
    notes: Optional[str] = None
    label: Optional[str] = None


class TrainingEvaluateRequest(BaseModel):
    candidate_id: Optional[str] = None
    instruction: Optional[str] = None
    ideal_output: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = 5
