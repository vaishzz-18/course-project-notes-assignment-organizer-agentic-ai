"""
EmbeddingService — Chunking and persistent embedding generation.
Uses Gemini's text-embedding-004 model when GEMINI_API_KEY is configured,
with a deterministic SHA256-seeded vector fallback for offline and local testing.
"""
import hashlib
import json
import math
from typing import List, Optional
from config import settings


class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = 768

    def compute_content_hash(self, text: str) -> str:
        """Computes SHA-256 hash for deduplication."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Splits document text into overlapping chunks respecting sentence/paragraph boundaries.
        """
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        if len(clean_text) <= chunk_size:
            return [clean_text]

        chunks = []
        start = 0
        text_len = len(clean_text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            # Try to snap to the nearest newline or period if possible
            if end < text_len:
                last_nl = clean_text.rfind("\n", start + chunk_size // 2, end)
                if last_nl != -1:
                    end = last_nl + 1
                else:
                    last_period = clean_text.rfind(". ", start + chunk_size // 2, end)
                    if last_period != -1:
                        end = last_period + 2

            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_len:
                break
            start = max(end - overlap, start + 1)

        return chunks

    def _fallback_embedding(self, text: str) -> List[float]:
        """
        Deterministic pseudo-embedding generated via hashing words and characters.
        Used when the external LLM provider is offline or credentials are not supplied.
        Produces normalized 768-dimensional float vector.
        """
        vec = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vec

        for idx, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            pos = h % self.dimension
            val = ((h >> 8) % 1000) / 1000.0 - 0.5
            vec[pos] += val * (1.0 / math.sqrt(idx + 1))

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_text(self, text: str) -> List[float]:
        """
        Generates embedding vector for a string.
        Attempts Gemini API call; falls back to deterministic vector if unavailable.
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document",
                )
                embedding = result.get("embedding", [])
                if embedding and len(embedding) > 0:
                    return list(embedding)
            except Exception:
                pass

        # Fallback to deterministic normalized vector
        return self._fallback_embedding(text)
