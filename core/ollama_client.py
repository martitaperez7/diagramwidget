"""
core/ollama_client.py
-----------------------
Talks to a LOCAL Ollama server (running the qwen3:4b model) to generate the
AI's text responses.

Covers:
    FR-14: send user messages to local Ollama (qwen3:4b) via HTTP
    FR-15: maintain full conversation history for context
    FR-16: run in a background thread so the UI never freezes
    FR-17: friendly error message if Ollama isn't running / times out
    FR-18: AI includes a [DIAGRAM: description] tag when a diagram would help
    NFR-02: responses should appear within ~30s on a 12GB RAM machine
    NFR-09: recover gracefully from connection failures, never crash
    NFR-12: all inference is local - no user data leaves the machine

Beginner notes:
    - Ollama exposes a simple local REST API (default http://localhost:11434).
    - PyQt's QThread lets us run a slow network call "in the background" so
      clicking buttons / typing doesn't freeze while we wait for a response.
      We communicate results back to the main UI thread using Qt "signals"
      (pyqtSignal), which is the thread-safe way to do it in PyQt5.
"""

import json
import re

import requests
from PyQt5.QtCore import QThread, pyqtSignal

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3:4b"
REQUEST_TIMEOUT_SECONDS = 60  # generous; NFR-02 expects ~30s in practice

# This system prompt is what teaches the local model to emit the
# [DIAGRAM: ...] tag (FR-18) whenever a visual would help the learner.
SYSTEM_PROMPT = (
    "You are Diagram Tutor, a friendly study assistant for visual learners. "
    "Explain concepts clearly and concisely. "
    "Whenever a diagram, flowchart, timeline, sequence, or mind map would "
    "help the user understand the topic better, end your response with a "
    "tag on its own line in this exact format: "
    "[DIAGRAM: short description of what to draw]. "
    "Only include the tag when a visual genuinely adds value - skip it for "
    "simple factual answers."
)

# Matches "[DIAGRAM: anything here]" anywhere in the text, case-insensitive.
DIAGRAM_TAG_PATTERN = re.compile(r"\[DIAGRAM:\s*(.+?)\]", re.IGNORECASE)


class OllamaWorker(QThread):
    """
    Runs a single chat request against Ollama on a background thread.

    Signals:
        response_ready(str, str): emitted with (display_text, diagram_description)
            display_text is the AI's reply with the [DIAGRAM: ...] tag stripped out.
            diagram_description is "" if no diagram tag was present.
        error_occurred(str): emitted with a friendly, plain-language error message.
    """

    response_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, conversation_history):
        super().__init__()
        # conversation_history is a list of {"role": ..., "content": ...}
        # dicts, owned by OllamaClient (FR-15: full history for context).
        self.conversation_history = conversation_history

    def run(self):
        payload = {
            "model": OLLAMA_MODEL,
            "messages": self.conversation_history,
            "stream": False,
        }
        try:
            response = requests.post(
                OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            data = response.json()
            raw_text = data.get("message", {}).get("content", "").strip()

            if not raw_text:
                self.error_occurred.emit(
                    "Ollama returned an empty response. Try asking again."
                )
                return

            diagram_match = DIAGRAM_TAG_PATTERN.search(raw_text)
            diagram_description = diagram_match.group(1).strip() if diagram_match else ""
            display_text = DIAGRAM_TAG_PATTERN.sub("", raw_text).strip()

            self.response_ready.emit(display_text, diagram_description)

        except requests.exceptions.ConnectionError:
            # FR-17 / NFR-06: plain language + suggested fix.
            self.error_occurred.emit(
                "Couldn't reach Ollama. Make sure it's installed and running "
                "- try opening a terminal and typing: ollama serve"
            )
        except requests.exceptions.Timeout:
            self.error_occurred.emit(
                "Ollama took too long to respond. It might be loading the "
                "model for the first time - please try again in a moment."
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            self.error_occurred.emit(
                "Ollama sent back a response we couldn't understand. "
                "Please try again."
            )
        except Exception as exc:  # NFR-09: never let an unexpected error crash the app
            self.error_occurred.emit(f"Unexpected error talking to Ollama: {exc}")


class OllamaClient:
    """
    Thin, UI-facing wrapper around OllamaWorker.

    The ChatPanel calls send_message() and connects to on_response /
    on_error to update the chat bubbles. This class owns the conversation
    history so it persists for the lifetime of the session (NFR-11).
    """

    def __init__(self):
        self.conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._worker = None

    def send_message(self, user_text, on_response, on_error):
        """
        FR-16: starts a background thread for the request so the UI
        stays responsive. on_response(display_text, diagram_description)
        and on_error(message) are callables (usually bound methods on the
        ChatPanel) invoked when the worker finishes.
        """
        self.conversation_history.append({"role": "user", "content": user_text})

        self._worker = OllamaWorker(list(self.conversation_history))

        def _handle_response(display_text, diagram_description):
            # Keep the raw AI reply (including the tag) in history so the
            # model retains full context of what it told the user.
            full_reply = display_text
            if diagram_description:
                full_reply += f" [DIAGRAM: {diagram_description}]"
            self.conversation_history.append({"role": "assistant", "content": full_reply})
            on_response(display_text, diagram_description)

        self._worker.response_ready.connect(_handle_response)
        self._worker.error_occurred.connect(on_error)
        self._worker.start()

    def clear_history(self):
        """Used by the 'new conversation' button planned for Step 6."""
        self.conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
