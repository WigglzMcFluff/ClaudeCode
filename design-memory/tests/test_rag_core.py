from __future__ import annotations

import unittest

from rag_config import database_name, validate_store
from rag_core import chunk_text


class StoreConfigurationTests(unittest.TestCase):
    def test_store_names_map_to_separate_databases(self) -> None:
        self.assertEqual(database_name("fusion360"), "fusion360_rag")
        self.assertEqual(database_name("blender"), "blender_rag")
        self.assertNotEqual(database_name("fusion360"), database_name("blender"))

    def test_invalid_store_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_store("shared")


class ChunkingTests(unittest.TestCase):
    def test_empty_text_produces_no_chunks(self) -> None:
        self.assertEqual(chunk_text("   \n\n  "), [])

    def test_short_paragraphs_are_kept_together(self) -> None:
        text = "First paragraph.\n\nSecond paragraph."
        self.assertEqual(chunk_text(text, max_characters=100), [text])

    def test_large_text_is_split_without_losing_words(self) -> None:
        text = " ".join(f"word{number}" for number in range(100))
        chunks = chunk_text(text, max_characters=80)
        rebuilt_words = " ".join(chunks).split()
        self.assertEqual(rebuilt_words, text.split())
        self.assertTrue(all(len(chunk) <= 80 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
