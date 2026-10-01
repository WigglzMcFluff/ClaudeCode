from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

from rag_config import (
    DB_HOST,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_NAME,
    MAX_CHUNK_CHARACTERS,
    database_name,
    minimum_similarity,
    validate_store,
)

SUPPORTED_EXTENSIONS = {".md", ".txt"}


@dataclass(frozen=True)
class SearchHit:
    source: str
    chunk_index: int
    similarity: float
    content: str


def connect(store: str):
    import psycopg
    from pgvector.psycopg import register_vector

    store = validate_store(store)
    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=database_name(store),
        user=DB_USER,
        password=DB_PASSWORD,
    )
    connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    connection.commit()
    register_vector(connection)
    ensure_schema(connection)
    return connection


def ensure_schema(connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id BIGSERIAL PRIMARY KEY,
            source_path TEXT NOT NULL,
            source_hash CHAR(64) NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR({EMBEDDING_DIMENSIONS}) NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (source_path, chunk_index)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS knowledge_chunks_source_path_idx "
        "ON knowledge_chunks (source_path)"
    )
    connection.commit()


@lru_cache(maxsize=1)
def embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_documents(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []

    vectors = embedding_model().encode_document(
        list(texts),
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [vector.tolist() for vector in vectors]


def embed_query(text: str) -> list[float]:
    vector = embedding_model().encode_query(
        text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vector.tolist()


def iter_knowledge_files(directory: Path) -> Iterable[Path]:
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{path} is not UTF-8 text.") from error


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chunk_text(text: str, max_characters: int = MAX_CHUNK_CHARACTERS) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    paragraphs = [
        re.sub(r"[ \t]+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", normalized)
        if paragraph.strip()
    ]

    pieces: list[str] = []
    for paragraph in paragraphs:
        pieces.extend(_split_large_paragraph(paragraph, max_characters))

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for piece in pieces:
        separator_length = 2 if current else 0
        proposed_length = current_length + separator_length + len(piece)

        if current and proposed_length > max_characters:
            chunks.append("\n\n".join(current))
            current = [piece]
            current_length = len(piece)
        else:
            current.append(piece)
            current_length = proposed_length

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def _split_large_paragraph(paragraph: str, max_characters: int) -> list[str]:
    if len(paragraph) <= max_characters:
        return [paragraph]

    words = paragraph.split()
    pieces: list[str] = []
    current: list[str] = []
    current_length = 0

    for word in words:
        separator_length = 1 if current else 0
        proposed_length = current_length + separator_length + len(word)

        if current and proposed_length > max_characters:
            pieces.append(" ".join(current))
            current = [word]
            current_length = len(word)
        else:
            current.append(word)
            current_length = proposed_length

    if current:
        pieces.append(" ".join(current))

    return pieces


def existing_source_hashes(connection) -> dict[str, str]:
    rows = connection.execute(
        """
        SELECT source_path, MAX(source_hash)
        FROM knowledge_chunks
        GROUP BY source_path
        """
    ).fetchall()
    return {source_path: source_hash for source_path, source_hash in rows}


def replace_source(
    connection,
    source_path: str,
    source_hash: str,
    chunks: Sequence[str],
) -> int:
    from pgvector import Vector

    connection.execute(
        "DELETE FROM knowledge_chunks WHERE source_path = %s",
        (source_path,),
    )

    if not chunks:
        connection.commit()
        return 0

    embedding_inputs = [
        f"Source: {source_path}\n\n{chunk}"
        for chunk in chunks
    ]
    embeddings = embed_documents(embedding_inputs)

    rows = [
        (
            source_path,
            source_hash,
            chunk_index,
            chunk,
            Vector(embedding),
        )
        for chunk_index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO knowledge_chunks (
                source_path,
                source_hash,
                chunk_index,
                content,
                embedding
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            rows,
        )

    connection.commit()
    return len(rows)


def delete_source(connection, source_path: str) -> None:
    connection.execute(
        "DELETE FROM knowledge_chunks WHERE source_path = %s",
        (source_path,),
    )
    connection.commit()


def search(store: str, query: str, limit: int = 5) -> list[SearchHit]:
    from pgvector import Vector

    store = validate_store(store)
    query = query.strip()
    if not query:
        raise ValueError("Search query cannot be empty.")
    if not 1 <= limit <= 20:
        raise ValueError("Search limit must be between 1 and 20.")

    query_vector = Vector(embed_query(query))
    min_similarity = minimum_similarity(store)

    with connect(store) as connection:
        rows = connection.execute(
            """
            SELECT source_path, chunk_index, similarity, content
            FROM (
                SELECT
                    source_path,
                    chunk_index,
                    1 - (embedding <=> %s) AS similarity,
                    content
                FROM knowledge_chunks
            ) AS ranked
            WHERE similarity >= %s
            ORDER BY similarity DESC
            LIMIT %s
            """,
            (query_vector, min_similarity, limit),
        ).fetchall()

    return [
        SearchHit(
            source=source_path,
            chunk_index=chunk_index,
            similarity=float(similarity),
            content=content,
        )
        for source_path, chunk_index, similarity, content in rows
    ]
