import tempfile
import unittest
from pathlib import Path

from backend.modules.assistant_session import LocalConversationMemory, WakePhraseMatcher


class WakePhraseMatcherTests(unittest.TestCase):
    def setUp(self):
        self.matcher = WakePhraseMatcher(["jarvis", "hey jarvis"])

    def test_accepts_both_phrases(self):
        self.assertEqual(self.matcher.extract_command("Jarvis, status"), "status")
        self.assertEqual(self.matcher.extract_command("Hey Jarvis open the dialer"), "open the dialer")

    def test_rejects_unaddressed_speech(self):
        self.assertIsNone(self.matcher.extract_command("open the dialer"))


class LocalConversationMemoryTests(unittest.TestCase):
    def test_persists_and_returns_last_user_message(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = LocalConversationMemory(Path(directory) / "conversation.json", max_turns=2)
            memory.append_exchange("First message", "First response")
            memory.append_exchange("Second message", "Second response")
            memory.append_exchange("Third message", "Third response")
            self.assertEqual(memory.last_user_message(), "Third message")
            self.assertEqual(len(memory.load()), 4)


if __name__ == "__main__":
    unittest.main()
