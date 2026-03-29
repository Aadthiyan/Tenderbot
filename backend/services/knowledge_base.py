"""
TenderBot Global — Knowledge Base Service
Handles vector embeddings and retrieval for company-specific RAG.
"""
import logging
import hashlib
import httpx
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import get_settings
from backend.services.db import get_db
from backend.services.encryption import encrypt_text, decrypt_text

logger = logging.getLogger(__name__)
settings = get_settings()

EMBEDDING_URL  = "https://api.fireworks.ai/inference/v1/embeddings"
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"


# ─── Chunking ──────────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Break large documents into smaller overlapping chunks."""
    if not text:
        return []
    chunks, start, text_len = [], 0, len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        if end == text_len:
            break
        start += chunk_size - overlap
    return chunks


# ─── Embedding ────────────────────────────────────────────────────────────────
async def get_embedding(text: str) -> List[float]:
    """Generates a vector embedding for the given text using Fireworks.ai."""
    if not settings.fireworks_api_key:
        logger.warning("No Fireworks API key found. Returning mock embedding.")
        return [0.0] * 768  # Nomic Embed size

    headers = {
        "Authorization": f"Bearer {settings.fireworks_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            EMBEDDING_URL,
            headers=headers,
            json={"model": EMBEDDING_MODEL, "input": text},
        )
        if resp.status_code != 200:
            logger.error(f"Embedding failed: {resp.text}")
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]


# ─── Vector search ────────────────────────────────────────────────────────────
async def search_knowledge_base(
    company_name: str, query: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """Performs a vector search in the knowledge base, filtered by company name."""
    query_vector = await get_embedding(query)
    db = get_db()

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": limit,
                "filter": {"company_name": company_name},
            }
        },
        {"$project": {"embedding": 0, "score": {"$meta": "vectorSearchScore"}}},
    ]

    cursor  = db["knowledge_base"].aggregate(pipeline)
    results = await cursor.to_list(length=limit)

    for row in results:
        if "text" in row:
            row["text"] = decrypt_text(row["text"])

    return results


# ─── Deduplication helper ─────────────────────────────────────────────────────
def _content_hash(text: str) -> str:
    """SHA-256 hash of the raw text, used for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def _document_exists(
    db,
    company_name: str,
    content_hash: Optional[str] = None,
    filename: Optional[str] = None,
) -> bool:
    """
    Returns True if a document with the same filename or content hash already
    exists in the knowledge base for this company.
    """
    query: Dict[str, Any] = {"company_name": company_name}
    if filename:
        query["metadata.filename"] = filename
    elif content_hash:
        query["content_hash"] = content_hash
    else:
        return False
    existing = await db["knowledge_base"].find_one(query, {"_id": 1})
    return existing is not None


# ─── Ingest ───────────────────────────────────────────────────────────────────
async def add_to_knowledge_base(
    company_name: str,
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Chunks, embeds, encrypts, and stores a piece of knowledge.
    Skips silently if the same filename or content hash already exists.
    Returns {"inserted": bool, "chunks": int}.
    """
    db       = get_db()
    filename = (metadata or {}).get("filename")
    hash_val = _content_hash(text)

    # ── Deduplication ──────────────────────────────────────────────────────────
    if await _document_exists(db, company_name, content_hash=hash_val, filename=filename):
        logger.info(
            f"Knowledge already stored for '{company_name}' "
            f"(file={filename or 'text'}, hash={hash_val[:8]}…). Skipping."
        )
        return {"inserted": False, "chunks": 0}
    # ──────────────────────────────────────────────────────────────────────────

    chunks = chunk_text(text)
    if not chunks:
        return {"inserted": False, "chunks": 0}

    now = datetime.utcnow()

    async def _build_doc(chunk: str, idx: int) -> Dict[str, Any]:
        embedding      = await get_embedding(chunk)
        encrypted_text = encrypt_text(chunk)
        chunk_meta     = dict(metadata or {})
        chunk_meta["chunk_index"] = idx
        return {
            "company_name": company_name,
            "text":         encrypted_text,
            "content_hash": hash_val,
            "metadata":     chunk_meta,
            "embedding":    embedding,
            "created_at":   now,
        }

    docs = await asyncio.gather(*[_build_doc(c, i) for i, c in enumerate(chunks)])

    if docs:
        await db["knowledge_base"].insert_many(list(docs))
        logger.info(f"Stored {len(docs)} chunks for '{company_name}'")

    return {"inserted": True, "chunks": len(docs)}
