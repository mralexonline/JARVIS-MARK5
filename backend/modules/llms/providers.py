"""LLM provider integrations for OpenAI (ChatGPT) and Anthropic (Claude).

Each provider reads its API key from the environment and exposes a simple
``chat(messages) -> str`` interface matching the existing ``pure_llama3`` shape
(``messages`` is a list of ``{"role", "content"}`` dicts). Use
``chat(provider, messages)`` to dispatch by name, or call a provider directly.

Keys are delivered via the platform secrets (``/run/base44/app.env``):
  - OPENAI_API_KEY      (https://platform.openai.com/api-keys)
  - ANTHROPIC_API_KEY   (https://console.anthropic.com/settings/keys)

Models are configurable through env vars with sensible defaults:
  - OPENAI_MODEL        (default: gpt-4o-mini)
  - ANTHROPIC_MODEL     (default: claude-3-5-sonnet-latest)
"""

import logging
import os

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")


def chat_with_openai(messages, model=None):
    """Send a chat completion to OpenAI and return the assistant text."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it on the Secrets page.")
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model or OPENAI_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content


def chat_with_anthropic(messages, model=None):
    """Send a chat completion to Anthropic (Claude) and return the assistant text.

    Anthropic takes the system prompt as a separate ``system`` parameter, so any
    ``system`` role messages are extracted and forwarded there.
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it on the Secrets page.")
    from anthropic import Anthropic

    system_parts = [m["content"] for m in messages if m.get("role") == "system"]
    convo = [m for m in messages if m.get("role") != "system"]

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=model or ANTHROPIC_MODEL,
        system="\n\n".join(system_parts) if system_parts else None,
        messages=convo,
        max_tokens=1024,
    )
    return response.content[0].text


_PROVIDERS = {
    "openai": chat_with_openai,
    "chatgpt": chat_with_openai,
    "anthropic": chat_with_anthropic,
    "claude": chat_with_anthropic,
}


def chat(provider, messages, model=None):
    """Dispatch a chat request to the named provider.

    Returns the assistant's text response, or an error string on failure so
    callers can surface it without crashing.
    """
    handler = _PROVIDERS.get((provider or "").lower())
    if handler is None:
        raise ValueError(f"Unknown LLM provider: {provider!r} "
                         f"(available: {', '.join(sorted(set(_PROVIDERS)))})")
    try:
        return handler(messages, model=model)
    except Exception as e:
        logger.error(f"{provider} chat failed: {e}")
        return f"An error occurred while contacting {provider}: {e}"
