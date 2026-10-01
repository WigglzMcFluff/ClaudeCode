from __future__ import annotations

import argparse

from rag_core import search


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search one local design-memory store from the command line."
    )
    parser.add_argument(
        "--store",
        required=True,
        choices=("fusion360", "blender"),
    )
    parser.add_argument("query", help="What you want to retrieve.")
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    results = search(arguments.store, arguments.query, arguments.limit)

    if not results:
        print("No sufficiently relevant indexed knowledge found.")
    else:
        for number, result in enumerate(results, start=1):
            print(f"\n[{number}] {result.source} — similarity {result.similarity:.3f}")
            print(result.content)
