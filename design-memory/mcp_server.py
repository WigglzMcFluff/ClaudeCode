from __future__ import annotations

import os
from typing import TypedDict

from mcp.server import MCPServer

from rag_config import validate_store
from rag_core import search


class DesignMemoryResult(TypedDict):
    source: str
    chunk_index: int
    similarity: float
    content: str


STORE = validate_store(os.environ.get("RAG_STORE", ""))
mcp = MCPServer(f"{STORE}-design-memory")


@mcp.tool()
def search_design_memory(query: str, limit: int = 5) -> list[DesignMemoryResult]:
    """Search verified local design knowledge for the active CAD tool.

    Use this before or during design work when prior requirements, physical print
    outcomes, measurements, user-confirmed decisions, or earlier failures may be
    relevant. Only knowledge above the configured relevance threshold is returned.
    An empty list means no sufficiently related stored knowledge was found. The server
    is scoped to a single CAD tool's isolated knowledge store.
    """
    return [
        {
            "source": hit.source,
            "chunk_index": hit.chunk_index,
            "similarity": round(hit.similarity, 4),
            "content": hit.content,
        }
        for hit in search(STORE, query, limit)
    ]


if __name__ == "__main__":
    mcp.run()
