"""Local RAG engine with optional ChromaDB and a lightweight fallback."""
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from config import CHROMA_DB_DIR, LOCAL_RAG_DIR

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def _safe_collection_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name.strip() or "default")
    return cleaned[:80] or "default"


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def _cosine_score(left: str, right: str) -> float:
    left_counts = Counter(_tokenize(left))
    right_counts = Counter(_tokenize(right))
    if not left_counts or not right_counts:
        return 0.0
    shared = set(left_counts) & set(right_counts)
    dot = sum(left_counts[token] * right_counts[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


class RAGEngine:
    def __init__(self):
        self.client = None
        self.model = None
        self.mode = "local"
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        LOCAL_RAG_DIR.mkdir(parents=True, exist_ok=True)

        if CHROMA_AVAILABLE:
            try:
                self.client = chromadb.Client(Settings(
                    persist_directory=str(CHROMA_DB_DIR),
                    anonymized_telemetry=False,
                ))
                self.model = SentenceTransformer(EMBEDDING_MODEL)
                self.mode = "chroma"
            except Exception as e:
                print(f"RAG Chroma init warning, using local fallback: {e}")
                self.client = None
                self.model = None
                self.mode = "local"

        self._initialized = True

    def _chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks."""
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if end < len(text):
                last_space = chunk.rfind(" ")
                if last_space > chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space + 1
            chunks.append(chunk.strip())
            start = max(end - overlap, start + 1)
        return chunks

    def _get_embedding(self, texts: List[str]) -> List[List[float]]:
        if not self.model:
            return []
        return self.model.encode(texts, convert_to_tensor=False).tolist()

    def _collection_path(self, collection_name: str) -> Path:
        return LOCAL_RAG_DIR / f"{_safe_collection_name(collection_name)}.json"

    def _load_local_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        path = self._collection_path(collection_name)
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _save_local_collection(self, collection_name: str, records: List[Dict[str, Any]]) -> None:
        path = self._collection_path(collection_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    async def ingest_document(self, content: str, filename: str, collection_name: str = "default") -> Dict[str, Any]:
        await self.initialize()
        collection_name = _safe_collection_name(collection_name)
        chunks = self._chunk_text(content)
        doc_id = hashlib.md5(f"{filename}:{content[:100]}".encode()).hexdigest()

        if self.mode == "chroma" and self.client and self.model:
            try:
                collection = self.client.get_or_create_collection(name=collection_name)
                existing = collection.get(ids=[doc_id])
                if existing and existing["ids"]:
                    return {"status": "already_exists", "chunks": 0, "collection": collection_name, "mode": self.mode}

                embeddings = self._get_embedding(chunks)
                chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
                metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

                collection.add(
                    ids=chunk_ids,
                    documents=chunks,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
                return {"status": "success", "chunks": len(chunks), "collection": collection_name, "doc_id": doc_id, "mode": self.mode}
            except Exception as e:
                print(f"RAG Chroma ingest warning, using local fallback: {e}")
                self.mode = "local"

        records = self._load_local_collection(collection_name)
        if any(record.get("doc_id") == doc_id for record in records):
            return {"status": "already_exists", "chunks": 0, "collection": collection_name, "mode": self.mode}

        for index, chunk in enumerate(chunks):
            records.append({
                "id": f"{doc_id}_chunk_{index}",
                "doc_id": doc_id,
                "source": filename,
                "chunk_index": index,
                "content": chunk,
            })
        self._save_local_collection(collection_name, records)
        return {"status": "success", "chunks": len(chunks), "collection": collection_name, "doc_id": doc_id, "mode": self.mode}

    async def query(self, question: str, collection_name: str = "default", top_k: int = 5) -> Dict[str, Any]:
        await self.initialize()
        collection_name = _safe_collection_name(collection_name)
        top_k = max(1, min(top_k, 20))

        if self.mode == "chroma" and self.client and self.model:
            try:
                collection = self.client.get_or_create_collection(name=collection_name)
                query_embedding = self._get_embedding([question])[0]
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"],
                )

                documents = []
                if results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        distance = float(results["distances"][0][i]) if results["distances"] and results["distances"][0] else 0.0
                        documents.append({
                            "content": doc,
                            "source": results["metadatas"][0][i].get("source", "unknown") if results["metadatas"][0] else "unknown",
                            "relevance": distance,
                        })
                context = "\n\n---\n\n".join([d["content"] for d in documents])
                return {"documents": documents, "context": context, "question": question, "collection": collection_name, "mode": self.mode}
            except Exception as e:
                print(f"RAG Chroma query warning, using local fallback: {e}")
                self.mode = "local"

        records = self._load_local_collection(collection_name)
        scored = []
        for record in records:
            score = _cosine_score(question, record["content"])
            if score > 0:
                scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)

        documents = [
            {
                "content": record["content"],
                "source": record.get("source", "unknown"),
                "relevance": 1.0 - score,
            }
            for score, record in scored[:top_k]
        ]
        context = "\n\n---\n\n".join([d["content"] for d in documents])
        return {"documents": documents, "context": context, "question": question, "collection": collection_name, "mode": self.mode}

    async def list_collections(self) -> List[str]:
        await self.initialize()
        names = {_safe_collection_name(path.stem) for path in LOCAL_RAG_DIR.glob("*.json")}

        if self.mode == "chroma" and self.client:
            try:
                names.update(c.name for c in self.client.list_collections())
            except Exception:
                pass

        return sorted(names or {"default"})

    async def delete_collection(self, name: str) -> bool:
        await self.initialize()
        name = _safe_collection_name(name)
        deleted = False

        local_path = self._collection_path(name)
        if local_path.exists():
            local_path.unlink()
            deleted = True

        if self.mode == "chroma" and self.client:
            try:
                self.client.delete_collection(name=name)
                deleted = True
            except Exception:
                pass
        return deleted

    async def collection_info(self, name: str) -> Dict[str, Any]:
        await self.initialize()
        name = _safe_collection_name(name)

        if self.mode == "chroma" and self.client:
            try:
                collection = self.client.get_or_create_collection(name=name)
                return {"name": name, "document_count": collection.count(), "mode": self.mode}
            except Exception:
                pass

        return {"name": name, "document_count": len(self._load_local_collection(name)), "mode": self.mode}


rag_engine = RAGEngine()
