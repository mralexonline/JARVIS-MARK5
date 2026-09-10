"""Safe wake-phrase matching and device-local conversation memory for JARVIS.

This module deliberately has no device-control or cloud-account access. Android
permissions and any external AI provider must be supplied by an authenticated
adapter that enforces the configured confirmation rules.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any, Iterable

DEFAULT_WAKE_PHRASES = ("jarvis", "hey jarvis")


class WakePhraseMatcher:
    def __init__(self, phrases: Iterable[str] = DEFAULT_WAKE_PHRASES) -> None:
        normalized = [self._normalize(value) for value in phrases if value.strip()]
        if not normalized:
            raise ValueError("At least one wake phrase is required")
        self.phrases = tuple(dict.fromkeys(normalized))
        alternatives = "|".join(re.escape(value) for value in sorted(self.phrases, key=len, reverse=True))
        self._pattern = re.compile(rf"^(?:{alternatives})\b[\s,.:;-]*(.*)$", re.IGNORECASE)

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    def extract_command(self, transcript: str) -> str | None:
        match = self._pattern.match(self._normalize(transcript))
        return match.group(1).strip() if match else None


class LocalConversationMemory:
    """Small JSON-backed transcript store intended for one local device."""

    def __init__(self, path: str | Path = "data/jarvis_conversation.json", max_turns: int = 40) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be positive")
        self.path = Path(path)
        self.max_messages = max_turns * 2
        self._lock = threading.Lock()

    def load(self) -> list[dict[str, str]]:
        with self._lock:
            if not self.path.exists():
                return []
            try:
                raw: Any = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return []
            if not isinstance(raw, list):
                return []
            return [
                {"role": item["role"], "content": item["content"]}
                for item in raw
                if isinstance(item, dict)
                and item.get("role") in {"user", "assistant"}
                and isinstance(item.get("content"), str)
            ][-self.max_messages :]

    def append_exchange(self, user_text: str, assistant_text: str) -> None:
        if not user_text.strip() or not assistant_text.strip():
            raise ValueError("Conversation messages cannot be empty")
        with self._lock:
            messages = self._load_unlocked()
            messages.extend(
                [
                    {"role": "user", "content": user_text.strip()},
                    {"role": "assistant", "content": assistant_text.strip()},
                ]
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(messages[-self.max_messages :], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.path)

    def last_user_message(self) -> str | None:
        for message in reversed(self.load()):
            if message["role"] == "user":
                return message["content"]
        return None

    def _load_unlocked(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return value if isinstance(value, list) else []
