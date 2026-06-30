"""
core/claude_client.py
-----------------------
Sends a diagram description (extracted from the local AI's [DIAGRAM: ...]
tag) to the Claude API and asks it to return either Mermaid diagram code
or a standalone SVG illustration.

Covers:
    FR-19: send the [DIAGRAM: ...] description to Claude
    FR-20: Claude decides Mermaid (flowchart/timeline/sequence/mind map) or SVG
    NFR-03: should complete within ~10s under normal network conditions
    NFR-10: graceful fallback message on Claude API failure
    NFR-13: API key comes from utils/config.py (.env), never hard-coded

Beginner notes:
    - We ask Claude to reply in a strict JSON shape: {"type": ..., "code": ...}
      so the rendering code (utils/diagram_render.py) always knows exactly
      what it's getting, instead of having to guess by parsing free text.
    - Like ollama_client.py, this runs on a background QThread so a slow
      Claude API call never freezes the UI (this satisfies the same
      "non-blocking" spirit as NFR-01, even though that NFR specifically
      names Ollama).
"""

import json
import re

from PyQt5.QtCore import QThread, pyqtSignal

from utils.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, has_claude_api_key

REQUEST_TIMEOUT_SECONDS = 30

DIAGRAM_SYSTEM_PROMPT = (
    "You generate diagrams for a study app called Diagram Tutor. "
    "Given a short topic description, decide whether it is better shown as "
    "a Mermaid diagram (flowchart, timeline, sequence diagram, or mind map - "
    "use 'mindmap' / 'graph' / 'timeline' / 'sequenceDiagram' syntax as "
    "appropriate) or as a small standalone SVG illustration. "
    "Respond with ONLY a single JSON object, no prose, no markdown code "
    "fences, in exactly this shape: "
    '{"type": "mermaid", "code": "..."} or {"type": "svg", "code": "..."}. '
    "For Mermaid, 'code' must be valid Mermaid syntax (no surrounding ``` "
    "fences). For SVG, 'code' must be a complete, self-contained <svg>...'"
    "</svg> element with explicit width/height. Keep diagrams compact and "
    "readable on a 350px-wide panel. "
    "Mermaid syntax rules - follow these exactly, they are common sources "
    "of parse errors: "
    "1) ALWAYS wrap every node label in double quotes, e.g. "
    'A["Start"] not A[Start], B{"arr[mid] == target?"} not B{arr[mid] == target?}. '
    "2) Inside a quoted label, NEVER use literal double quotes, square "
    "brackets, curly braces, or pipe characters - rewrite them in plain "
    "words instead (e.g. write 'array at index mid equals target' instead "
    "of 'arr[mid] == target'). "
    "3) For line breaks inside a label use <br/>, not a literal newline or "
    "backslash-n. "
    "4) Keep edge labels short and also quoted, e.g. "
    'A -->|"yes"| B. '
    "5) Use only plain letters, numbers, spaces, and basic punctuation "
    "(. , ! ? : -) inside labels - avoid mathematical/code symbols like "
    "==, !=, <, >, &&, || even inside quotes, since some renderers still "
    "choke on them. Spell them out instead (e.g. 'equals', 'is greater "
    "than')."
)


def _extract_json_object(text: str) -> dict:
    """
    Claude is asked to return raw JSON, but models occasionally wrap output
    in ```json fences anyway. This pulls out the first {...} block so
    parsing doesn't break on minor formatting slip-ups.
    """
    fence_match = re.search(r"\{.*\}", text, re.DOTALL)
    if not fence_match:
        raise ValueError("No JSON object found in Claude's response.")
    return json.loads(fence_match.group(0))


class ClaudeWorker(QThread):
    """
    Background worker that calls the Claude API once and reports back via
    signals (mirrors the OllamaWorker pattern for consistency).

    Signals:
        diagram_ready(str, str): (diagram_type, diagram_code) where
            diagram_type is "mermaid" or "svg".
        error_occurred(str): friendly, plain-language error message.
    """

    diagram_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, description: str):
        super().__init__()
        self.description = description

    def run(self):
        if not has_claude_api_key():
            self.error_occurred.emit(
                "No Claude API key found. Add ANTHROPIC_API_KEY to your "
                ".env file to enable diagram generation."
            )
            return

        try:
            # Imported here (not at module top) so the whole app doesn't
            # fail to start if the 'anthropic' package isn't installed yet
            # - the rest of the chat still works without diagrams.
            import anthropic

            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1500,
                system=DIAGRAM_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": self.description}],
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            raw_text = "".join(
                block.text for block in message.content if hasattr(block, "text")
            )
            parsed = _extract_json_object(raw_text)

            diagram_type = parsed.get("type", "").lower().strip()
            diagram_code = parsed.get("code", "").strip()

            if diagram_type not in ("mermaid", "svg") or not diagram_code:
                self.error_occurred.emit(
                    "Claude returned an unexpected diagram format. "
                    "Showing text explanation only."
                )
                return

            self.diagram_ready.emit(diagram_type, diagram_code)

        except ImportError:
            self.error_occurred.emit(
                "The 'anthropic' package isn't installed. Run: "
                "pip install anthropic"
            )
        except (ValueError, json.JSONDecodeError):
            self.error_occurred.emit(
                "Couldn't understand Claude's diagram response. "
                "Showing text explanation only."
            )
        except Exception as exc:
            # NFR-10: graceful fallback covering auth errors, rate limits,
            # timeouts, and any other Claude API failure - never crash.
            message_text = str(exc).lower()
            if "authentication" in message_text or "api key" in message_text:
                friendly = (
                    "Claude rejected the API key. Double-check "
                    "ANTHROPIC_API_KEY in your .env file."
                )
            elif "rate limit" in message_text or "429" in message_text:
                friendly = "Claude's rate limit was hit. Please try again shortly."
            elif "timeout" in message_text or "timed out" in message_text:
                friendly = "Claude took too long to respond. Please try again."
            else:
                friendly = f"Couldn't generate a diagram right now: {exc}"
            self.error_occurred.emit(friendly)


class ClaudeClient:
    """UI-facing wrapper, mirrors OllamaClient's interface for consistency."""

    def __init__(self):
        self._worker = None

    def generate_diagram(self, description: str, on_ready, on_error):
        """
        Starts the background Claude request.
        on_ready(diagram_type, diagram_code) and on_error(message) are
        callables invoked when the worker finishes (FR-21/FR-22 rendering
        and loading-placeholder logic live in chat_panel.py / diagram_render.py).
        """
        self._worker = ClaudeWorker(description)
        self._worker.diagram_ready.connect(on_ready)
        self._worker.error_occurred.connect(on_error)
        self._worker.start()
