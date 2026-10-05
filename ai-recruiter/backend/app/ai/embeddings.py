import numpy as np
from typing import List, Union
from app.config import settings

_model = None


def get_embedding_model():
    """Lazy load SentenceTransformer model singleton."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print(f"[*] Loading SentenceTransformer model '{settings.EMBEDDING_MODEL_NAME}'...")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            print("[+] Embedding model loaded successfully.")
        except Exception as e:
            print(f"[!] Warning: Could not load SentenceTransformer: {e}")
            _model = None
    return _model


def generate_embedding(text: str) -> np.ndarray:
    """Generate dense 384-dimensional normalized embedding vector for input text."""
    if not text or not text.strip():
        return np.zeros(384, dtype=np.float32)

    model = get_embedding_model()
    if model is None:
        # Fallback: simple deterministic hash vector for testing/offline mode
        return _deterministic_fallback_vector(text)

    # Clean text to 512 tokens max
    clean_text = text[:1500].strip()
    embedding = model.encode(clean_text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.astype(np.float32)


def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two normalized vectors, returning 0.0 to 100.0."""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0.0 or norm2 == 0.0:
        return 50.0  # Neutral baseline if vector is empty

    dot_product = np.dot(vec1, vec2)
    similarity = dot_product / (norm1 * norm2)

    # Scale from [-1.0, 1.0] to [0.0, 100.0]%
    score = ((float(similarity) + 1.0) / 2.0) * 100.0
    return max(0.0, min(100.0, round(score, 1)))


def calculate_text_semantic_similarity(text1: str, text2: str) -> float:
    """Directly calculate semantic similarity percentage between two text strings."""
    vec1 = generate_embedding(text1)
    vec2 = generate_embedding(text2)
    return calculate_cosine_similarity(vec1, vec2)


def _deterministic_fallback_vector(text: str) -> np.ndarray:
    """Deterministic 384-d pseudo-embedding generator using token hashing for offline fallback."""
    words = text.lower().split()
    vec = np.zeros(384, dtype=np.float32)
    for i, w in enumerate(words):
        val = sum(ord(c) for c in w)
        idx = (val + i) % 384
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


class EmbeddingService:
    @staticmethod
    def get_embedding(text: str) -> np.ndarray:
        return generate_embedding(text)

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        return calculate_cosine_similarity(vec1, vec2)


embedding_service = EmbeddingService()

