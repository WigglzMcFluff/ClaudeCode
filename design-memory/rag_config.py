from __future__ import annotations

import os
from pathlib import Path

SUPPORTED_STORES = ("fusion360", "blender")
STORE_DATABASES = {
    "fusion360": "fusion360_rag",
    "blender": "blender_rag",
}
MIN_SIMILARITY_BY_STORE = {
    "fusion360": 0.30,
    "blender": 0.30,
}

DB_HOST = os.getenv("RAG_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("RAG_DB_PORT", "5432"))
DB_USER = os.getenv("RAG_DB_USER", "rag")
DB_PASSWORD = os.getenv("RAG_DB_PASSWORD", "rag")

EMBEDDING_MODEL_NAME = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
EMBEDDING_DIMENSIONS = 384
MAX_CHUNK_CHARACTERS = 1_200

PROJECT_ROOT = Path(__file__).resolve().parent


def validate_store(store: str) -> str:
    normalized = store.strip().lower()
    if normalized not in STORE_DATABASES:
        valid = ", ".join(SUPPORTED_STORES)
        raise ValueError(f"Unknown store '{store}'. Expected one of: {valid}.")
    return normalized


def database_name(store: str) -> str:
    return STORE_DATABASES[validate_store(store)]


def minimum_similarity(store: str) -> float:
    return MIN_SIMILARITY_BY_STORE[validate_store(store)]


def knowledge_directory(store: str) -> Path:
    return PROJECT_ROOT / "knowledge" / validate_store(store)
