from __future__ import annotations

from rag_config import EMBEDDING_DIMENSIONS, SUPPORTED_STORES
from rag_core import connect, embed_query


def main() -> None:
    vector = embed_query("Local design-memory setup check.")
    if len(vector) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Embedding model returned {len(vector)} dimensions; "
            f"expected {EMBEDDING_DIMENSIONS}."
        )

    for store in SUPPORTED_STORES:
        with connect(store) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM knowledge_chunks"
            ).fetchone()[0]
        print(f"{store}: database reachable, {count} indexed chunks")

    print(f"embedding model: {len(vector)} dimensions")
    print("setup check passed")


if __name__ == "__main__":
    main()
