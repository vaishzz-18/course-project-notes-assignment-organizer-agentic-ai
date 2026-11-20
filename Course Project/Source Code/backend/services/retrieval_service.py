"""
RetrievalService — Course-aware semantic retrieval over persistent document embeddings.
Enforces course-level access isolation: never returns chunks from unauthorized courses.
"""
import json
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from models.database import DocumentChunk, Note
from services.embedding_service import EmbeddingService


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class RetrievalService:
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedder = embedding_service or EmbeddingService()

    async def index_note(
        self,
        db: AsyncSession,
        note_id: int,
        course_id: int,
        text: str,
    ) -> int:
        """
        Chunks and indexes note text. Avoids re-indexing duplicate chunks using content_hash.
        Returns number of new chunks indexed.
        """
        chunks = self.embedder.chunk_text(text)
        if not chunks:
            return 0

        indexed_count = 0
        for idx, chunk_text in enumerate(chunks):
            content_hash = self.embedder.compute_content_hash(chunk_text)

            # Check if this exact chunk hash already exists for this note
            q = select(DocumentChunk).where(
                and_(
                    DocumentChunk.note_id == note_id,
                    DocumentChunk.content_hash == content_hash,
                )
            )
            res = await db.execute(q)
            if res.scalar_one_or_none():
                continue

            vector = self.embedder.embed_text(chunk_text)
            doc_chunk = DocumentChunk(
                note_id=note_id,
                course_id=course_id,
                chunk_index=idx,
                chunk_text=chunk_text,
                content_hash=content_hash,
                embedding_model=self.embedder.model_name,
                embedding_json=json.dumps(vector),
                access_scope="course",
            )
            db.add(doc_chunk)
            indexed_count += 1

        if indexed_count > 0:
            await db.flush()
        return indexed_count

    async def search(
        self,
        db: AsyncSession,
        query: str,
        course_id: int,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k semantically relevant chunks strictly within course_id scope.
        Returns chunk text with note citation metadata.
        """
        if not query or not query.strip():
            return []

        query_vec = self.embedder.embed_text(query)

        # Retrieve all chunks for this course
        q = (
            select(DocumentChunk, Note)
            .join(Note, DocumentChunk.note_id == Note.id)
            .where(DocumentChunk.course_id == course_id)
        )
        res = await db.execute(q)
        rows = res.all()

        if not rows:
            return []

        scored_results = []
        for chunk, note in rows:
            if not chunk.embedding_json:
                continue
            chunk_vec = json.loads(chunk.embedding_json)
            score = cosine_similarity(query_vec, chunk_vec)
            scored_results.append({
                "chunk_id": chunk.id,
                "note_id": note.id,
                "note_title": note.title,
                "unit": note.unit,
                "topic": note.topic,
                "chunk_index": chunk.chunk_index,
                "text": chunk.chunk_text,
                "similarity_score": round(score, 4),
            })

        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_results[:top_k]
