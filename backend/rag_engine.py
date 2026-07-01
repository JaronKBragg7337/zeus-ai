"""Local RAG engine using sentence-transformers and ChromaDB."""
import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

class RAGEngine:
    def __init__(self):
        self.client = None
        self.model = None
        self._initialized = False

    async def initialize(self):
        if self._initialized or not RAG_AVAILABLE:
            return
        try:
            self.client = chromadb.Client(Settings(
                persist_directory=DB_PATH,
                anonymized_telemetry=False
            ))
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            self._initialized = True
        except Exception as e:
            print(f"RAG init warning: {e}")

    def _chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks."""
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space + 1
            chunks.append(chunk.strip())
            start = end - overlap
        return chunks

    def _get_embedding(self, texts: List[str]) -> List[List[float]]:
        if not self.model:
            return []
        return self.model.encode(texts, convert_to_tensor=False).tolist()

    async def ingest_document(self, content: str, filename: str, collection_name: str = "default") -> Dict[str, Any]:
        await self.initialize()
        if not self._initialized:
            return {"error": "RAG not available. Install sentence-transformers and chromadb."}

        try:
            collection = self.client.get_or_create_collection(name=collection_name)
            doc_id = hashlib.md5(f"{filename}:{content[:100]}".encode()).hexdigest()
            existing = collection.get(ids=[doc_id])
            if existing and existing["ids"]:
                return {"status": "already_exists", "chunks": 0, "collection": collection_name}

            chunks = self._chunk_text(content)
            embeddings = self._get_embedding(chunks)

            chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

            collection.add(
                ids=chunk_ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas
            )

            return {"status": "success", "chunks": len(chunks), "collection": collection_name, "doc_id": doc_id}
        except Exception as e:
            return {"error": str(e)}

    async def query(self, question: str, collection_name: str = "default", top_k: int = 5) -> Dict[str, Any]:
        await self.initialize()
        if not self._initialized:
            return {"error": "RAG not available"}

        try:
            collection = self.client.get_or_create_collection(name=collection_name)
            query_embedding = self._get_embedding([question])[0]

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            documents = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    documents.append({
                        "content": doc,
                        "source": results["metadatas"][0][i].get("source", "unknown") if results["metadatas"][0] else "unknown",
                        "relevance": float(results["distances"][0][i]) if results["distances"] and results["distances"][0] else 0.0
                    })

            context = "\n\n---\n\n".join([d["content"] for d in documents])
            return {"documents": documents, "context": context, "question": question}
        except Exception as e:
            return {"error": str(e)}

    async def list_collections(self) -> List[str]:
        await self.initialize()
        if not self._initialized:
            return []
        try:
            return [c.name for c in self.client.list_collections()]
        except Exception:
            return []

    async def delete_collection(self, name: str) -> bool:
        await self.initialize()
        if not self._initialized:
            return False
        try:
            self.client.delete_collection(name=name)
            return True
        except Exception:
            return False

    async def collection_info(self, name: str) -> Dict[str, Any]:
        await self.initialize()
        if not self._initialized:
            return {"error": "RAG not available"}
        try:
            collection = self.client.get_or_create_collection(name=name)
            count = collection.count()
            return {"name": name, "document_count": count}
        except Exception as e:
            return {"error": str(e)}


rag_engine = RAGEngine()
