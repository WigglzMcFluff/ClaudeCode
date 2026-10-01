from __future__ import annotations

import argparse
from pathlib import Path

from rag_config import knowledge_directory, validate_store
from rag_core import (
    chunk_text,
    connect,
    delete_source,
    existing_source_hashes,
    iter_knowledge_files,
    read_text_file,
    replace_source,
    sha256_file,
)


def seed_store(store: str, directory: Path | None = None) -> None:
    store = validate_store(store)
    directory = (directory or knowledge_directory(store)).resolve()

    if not directory.exists():
        raise FileNotFoundError(f"Knowledge directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Knowledge path is not a directory: {directory}")

    files = list(iter_knowledge_files(directory))
    current_sources = {
        path.relative_to(directory).as_posix(): path
        for path in files
    }

    added_or_updated = 0
    unchanged = 0
    removed = 0
    written_chunks = 0

    with connect(store) as connection:
        indexed_hashes = existing_source_hashes(connection)

        for source_path, file_path in current_sources.items():
            source_hash = sha256_file(file_path)
            if indexed_hashes.get(source_path) == source_hash:
                unchanged += 1
                continue

            text = read_text_file(file_path)
            chunks = chunk_text(text)
            written_chunks += replace_source(
                connection,
                source_path,
                source_hash,
                chunks,
            )
            added_or_updated += 1

        stale_sources = sorted(set(indexed_hashes) - set(current_sources))
        for source_path in stale_sources:
            delete_source(connection, source_path)
            removed += 1

    print(f"Store: {store}")
    print(f"Directory: {directory}")
    print(f"Added or updated files: {added_or_updated}")
    print(f"Unchanged files: {unchanged}")
    print(f"Removed files: {removed}")
    print(f"Written chunks: {written_chunks}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize one local knowledge directory into its pgvector store."
    )
    parser.add_argument(
        "--store",
        required=True,
        choices=("fusion360", "blender"),
        help="Which isolated design-memory store to seed.",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        help="Optional directory override. Defaults to knowledge/<store>.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    seed_store(arguments.store, arguments.directory)
