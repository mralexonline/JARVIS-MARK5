# JARVIS mobile voice integration

The configured wake phrases are **“Jarvis”** and **“Hey Jarvis.”**

## What is operational

- The private control panel can recognise either phrase after the user taps its microphone.
- Browser speech synthesis provides spoken replies.
- The most recent 40 exchanges are stored in that browser's local storage.
- Dialer and WhatsApp hand-offs require an explicit confirmation.
- `backend/modules/assistant_session.py` provides equivalent wake matching and local JSON memory for the Python runtime.

## Required Android bridge

Permanent background or lock-screen wake listening requires a signed Android application with a foreground microphone service, a persistent notification, runtime permission handling, and an on-device hotword engine. The legacy JARVIS-MARK5 repository is a desktop Python/Eel application and cannot be installed as that Android service unchanged.

The Android bridge should send recognised text to the assistant only after matching a configured wake phrase. Calls, messages, contact access and other sensitive actions must remain denied by default and pass through an explicit confirmation screen.

## ChatGPT boundary

A third-party dashboard cannot read or merge a user's private ChatGPT account memory through a public browser API. The control panel therefore offers a user-initiated hand-off to ChatGPT Voice while keeping its own recent transcript on the device.

A future OpenAI API integration would require a server-side API key, separate conversation storage and explicit consent. It would be a distinct API conversation—not a covert mirror of ChatGPT account memory.
