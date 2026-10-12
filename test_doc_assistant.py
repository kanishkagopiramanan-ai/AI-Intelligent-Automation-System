"""Unit tests for Module 2: Document Support Assistant."""

import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.doc_reader import (
    clean_text,
    chunk_sections,
    tokenize,
    retrieve_relevant_chunks,
    detect_topic_change,
    detect_repeated_question,
    answer_document_query,
)


class TestDocumentAssistant(unittest.TestCase):
    def setUp(self):
        self.sample_sections = [
            {
                "filename": "policy.txt",
                "page_or_section": "Section 1: Grace Period",
                "page_num": 1,
                "text": "A grace period of thirty calendar days is allowed for overdue premiums. During this grace period, the policy remains in full force and coverage continues without penalty."
            },
            {
                "filename": "policy.txt",
                "page_or_section": "Section 2: Free Look",
                "page_num": 2,
                "text": "The customer has a free-look period of fifteen days from receiving the policy to review all terms and conditions or cancel with full refund."
            },
            {
                "filename": "policy.txt",
                "page_or_section": "Section 3: Claims",
                "page_num": 3,
                "text": "To file a claim, submit the death certificate, original policy certificate, and KYC documents within 30 days."
            }
        ]
        self.chunks = chunk_sections(self.sample_sections)

    def test_chunking(self):
        self.assertGreaterEqual(len(self.chunks), 3)
        self.assertEqual(self.chunks[0]["filename"], "policy.txt")

    def test_retrieval(self):
        retrieved = retrieve_relevant_chunks(self.chunks, "What is the grace period?", top_k=1)
        self.assertEqual(len(retrieved), 1)
        self.assertIn("grace period", retrieved[0]["text"].lower())
        self.assertGreater(retrieved[0]["confidence"], 0.5)

    def test_topic_change_detection(self):
        # Grace period -> free look = topic shift
        is_shift = detect_topic_change("How do I cancel during free look?", "What is the grace period for payment?")
        self.assertTrue(is_shift)

        # Same topic follow-up
        is_shift_same = detect_topic_change("How many days is that grace period?", "What is the grace period for payment?")
        self.assertFalse(is_shift_same)

    def test_repeated_question_detection(self):
        history = [
            {"role": "user", "content": "What is the grace period?"},
            {"role": "assistant", "content": "30 days"}
        ]
        is_repeat = detect_repeated_question("What is the grace period?", history)
        self.assertTrue(is_repeat)

        not_repeat = detect_repeated_question("What is the free look period?", history)
        self.assertFalse(not_repeat)

    def test_answer_synthesis(self):
        history = []
        result = answer_document_query("What is the grace period for overdue premiums?", self.chunks, history)
        self.assertIn("thirty calendar days", result["answer"])
        self.assertGreaterEqual(len(result["sources"]), 1)
        self.assertIn("policy.txt", result["sources"][0]["filename"])


if __name__ == "__main__":
    unittest.main()
