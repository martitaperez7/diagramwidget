"""
ui/chat_panel.py
------------------
Chat area — UMBC Whimsy Academia redesign.

Key UX changes from original:
  - DIAGRAM appears FIRST, before the text explanation
  - AI response is trimmed to 2-3 bullet points by default
  - "Read more ↓" button expands the full explanation
  - Parchment-toned AI bubbles (warm off-white on dark background)
  - Gold typing indicator
  - Diagram section gets a gold italic label above it

Covers all original FRs:
    FR-07  submit via Enter or send button
    FR-08  user messages right-aligned (gold bubbles)
    FR-09  AI responses left-aligned (parchment bubbles)
    FR-10  animated typing indicator
    FR-11  input disabled while pending
    FR-12  auto-scroll to latest message
    FR-13  bubble text selectable/copyable
    FR-19/21/22  Claude diagram trigger, loading placeholder, render
    NFR-06 plain-language errors in banner
"""

import re

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)

from core.ollama_client import OllamaClient
from core.claude_client import ClaudeClient
from utils.diagram_render import DiagramLoadingPlaceholder, build_diagram_widget

# Maximum width for message bubbles — wider so they fill the panel better
BUBBLE_MAX_WIDTH = 340

# How many bullet points to show before the "Read more" button
MAX_VISIBLE_BULLETS = 3


def _parse_to_bullets(text: str) -> list:
    """
    Converts an AI response into a list of content blocks.

    Each item in the returned list is either:
      - A string  → a plain bullet point
      - A dict    → {"type": "code", "lang": "python", "code": "..."}

    Strategy:
      1. Extract code blocks (```lang ... ```) first, preserve them as dicts
      2. For remaining text, strip markdown bold and split into bullets
      3. If one giant blob, split on sentences instead
    """
    # Remove markdown bold markers
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)

    # Split on code fences — pattern: ```lang\ncode\n```
    # re.split with a capturing group keeps the matched parts in the list
    parts = re.split(r"(```[\w]*\n[\s\S]*?```)", text)

    result = []

    for part in parts:
        # ── Code block ──────────────────────────────────────────────
        if part.startswith("```"):
            lines = part.splitlines()
            lang = lines[0].replace("```", "").strip() or "code"
            code = "\n".join(lines[1:]).rstrip("`").strip()
            result.append({"type": "code", "lang": lang, "code": code})
            continue

        # ── Plain text — split into bullets ─────────────────────────
        for line in part.splitlines():
            line = line.strip()
            if not line:
                continue
            # Strip list markers: "1.", "-", "•", "*"
            line = re.sub(r"^[\d]+\.\s*", "", line)
            line = re.sub(r"^[-•*]\s*", "", line)
            if line:
                result.append(line)

    # If we ended up with just one giant text blob, split on sentences
    if len(result) == 1 and isinstance(result[0], str) and len(result[0]) > 120:
        sentences = re.split(r"(?<=[.!?])\s+", result[0])
        result = [s.strip() for s in sentences if s.strip()]

    return result


class AIResponseWidget(QWidget):
    """
    Displays an AI text response as ONE parchment bubble containing
    all bullet points, with a 'Read more' button below if needed.

    Fix from original:
      - All bullets share ONE styled bubble box (not one box per bullet)
      - Read More button sits OUTSIDE the bubble, below it
      - Bubble stretches to fill panel width properly

    Layout:
      ┌─────────────────────────────────┐
      │ • Bullet one text here          │  <- ONE parchment bubble
      │ • Bullet two text here          │
      │ • Bullet three text here        │
      └─────────────────────────────────┘
        [Read more down]                   <- outside bubble, only if needed
    """

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._bullets = _parse_to_bullets(text)
        self._bullet_labels = []
        self._expanded = False

        # Outer layout: bubble on top, button below
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        # ── Single parchment bubble container ─────────────────────────
        # This QWidget gets the AIBubble style — all bullets share
        # one background box rather than each having their own.
        self._bubble_box = QWidget()
        self._bubble_box.setObjectName("AIBubble")
        self._bubble_box.setMaximumWidth(BUBBLE_MAX_WIDTH)

        bubble_layout = QVBoxLayout(self._bubble_box)
        bubble_layout.setContentsMargins(10, 10, 10, 10)
        bubble_layout.setSpacing(6)

        # One widget per block: bullet label OR styled code box
        for block in self._bullets:
            if isinstance(block, dict) and block.get("type") == "code":
                # Code block: dark monospace box with gold language label
                code_container = QWidget()
                code_container.setStyleSheet(
                    "background-color: #0D0D0D; "
                    "border: 1px solid #F0B400; "
                    "border-radius: 6px;"
                )
                code_layout = QVBoxLayout(code_container)
                code_layout.setContentsMargins(8, 6, 8, 6)
                code_layout.setSpacing(4)

                lang_label = QLabel(block.get("lang", "code"))
                lang_label.setStyleSheet(
                    "color: #F0B400; font-family: Georgia, serif; "
                    "font-size: 10px; font-style: italic; "
                    "background: transparent; border: none;"
                )
                code_layout.addWidget(lang_label)

                code_label = QLabel(block["code"])
                code_label.setWordWrap(True)
                code_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                code_label.setStyleSheet(
                    "color: #FAF3DC; font-family: Consolas, monospace; "
                    "font-size: 11px; background: transparent; border: none;"
                )
                code_layout.addWidget(code_label)
                bubble_layout.addWidget(code_container)
                self._bullet_labels.append(code_container)
            else:
                # Plain bullet point
                label = QLabel(f"• {block}")
                label.setWordWrap(True)
                label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
                label.setStyleSheet(
                    "color: #FAF3DC; font-family: Georgia, serif; "
                    "font-size: 12px; background: transparent; border: none;"
                )
                bubble_layout.addWidget(label)
                self._bullet_labels.append(label)

        outer.addWidget(self._bubble_box)

        # ── Read more button (outside the bubble) ──────────────────────
        self._read_more_btn = QPushButton("Read more")
        self._read_more_btn.setObjectName("ReadMoreButton")
        self._read_more_btn.setMaximumWidth(BUBBLE_MAX_WIDTH)
        self._read_more_btn.clicked.connect(self._toggle_expand)
        outer.addWidget(self._read_more_btn)

        self._apply_visibility()

    def _apply_visibility(self):
        """Show first MAX_VISIBLE_BULLETS; hide the rest until expanded."""
        has_extra = len(self._bullets) > MAX_VISIBLE_BULLETS

        for i, label in enumerate(self._bullet_labels):
            label.setVisible(self._expanded or i < MAX_VISIBLE_BULLETS)

        if not has_extra:
            self._read_more_btn.hide()
        else:
            self._read_more_btn.setText(
                "Read less" if self._expanded else "Read more"
            )
            self._read_more_btn.show()

    def _toggle_expand(self):
        self._expanded = not self._expanded
        self._apply_visibility()


class ChatPanel(QWidget):
    """
    Full chat panel with UMBC whimsy academia styling.

    Message order for each AI turn:
      1. [Gold label]  ✦ Visual Overview
      2. [Diagram]     rendered Mermaid / SVG (or loading placeholder)
      3. [Parchment]   AI text as bullet points + Read More button
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ollama_client = OllamaClient()
        self.claude_client = ClaudeClient()

        self._typing_label = None
        self._typing_timer = None
        self._typing_dot_count = 0

        self._build_ui()

    # ──────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Scrollable message feed ────────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ChatScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.message_container = QWidget()
        self.message_container.setObjectName("ChatContainer")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(10, 10, 10, 10)
        self.message_layout.setSpacing(6)   # Tighter spacing between messages
        self.message_layout.addStretch(1)

        self.scroll_area.setWidget(self.message_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # ── Error banner ───────────────────────────────────────────────
        self.error_banner = QLabel("")
        self.error_banner.setObjectName("ErrorBanner")
        self.error_banner.setWordWrap(True)
        self.error_banner.hide()
        layout.addWidget(self.error_banner)

        # ── Input row ──────────────────────────────────────────────────
        input_row = QHBoxLayout()
        input_row.setContentsMargins(12, 8, 12, 12)
        input_row.setSpacing(8)

        self.message_input = QLineEdit()
        self.message_input.setObjectName("MessageInput")
        self.message_input.setPlaceholderText("Ask about any topic…")
        self.message_input.returnPressed.connect(self._on_send_clicked)
        input_row.addWidget(self.message_input, stretch=1)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("SendButton")
        self.send_button.clicked.connect(self._on_send_clicked)
        input_row.addWidget(self.send_button)

        layout.addLayout(input_row)

    # ──────────────────────────────────────────────────────────────────
    # Sending a message
    # ──────────────────────────────────────────────────────────────────
    def _on_send_clicked(self):
        text = self.message_input.text().strip()
        if not text:
            return

        self._add_user_bubble(text)
        self.message_input.clear()
        self._set_input_enabled(False)
        self._hide_error()
        self._show_typing_indicator()

        self.ollama_client.send_message(
            text,
            on_response=self._on_ollama_response,
            on_error=self._on_ollama_error,
        )

    def _set_input_enabled(self, enabled: bool):
        self.message_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        if enabled:
            self.message_input.setFocus()

    # ──────────────────────────────────────────────────────────────────
    # Typing indicator (FR-10)
    # ──────────────────────────────────────────────────────────────────
    def _show_typing_indicator(self):
        self._typing_label = QLabel("✦ thinking")
        self._typing_label.setObjectName("TypingIndicator")
        self.message_layout.insertWidget(
            self.message_layout.count() - 1, self._typing_label
        )
        self._typing_dot_count = 0
        self._typing_timer = QTimer(self)
        self._typing_timer.timeout.connect(self._animate_typing_dots)
        self._typing_timer.start(400)
        self._scroll_to_bottom()

    def _animate_typing_dots(self):
        self._typing_dot_count = (self._typing_dot_count + 1) % 4
        dots = "·" * self._typing_dot_count
        if self._typing_label is not None:
            self._typing_label.setText(f"✦ thinking{dots}")

    def _hide_typing_indicator(self):
        if self._typing_timer:
            self._typing_timer.stop()
            self._typing_timer = None
        if self._typing_label:
            self._typing_label.deleteLater()
            self._typing_label = None

    # ──────────────────────────────────────────────────────────────────
    # Ollama response (FR-09)
    # ──────────────────────────────────────────────────────────────────
    def _on_ollama_response(self, display_text: str, diagram_description: str):
        self._hide_typing_indicator()
        self._set_input_enabled(True)

        if diagram_description:
            # ── DIAGRAM FIRST, then text explanation ───────────────────
            # 1. Gold section label
            self._add_section_label("✦ Visual Overview")

            # 2. Diagram loading placeholder (replaced when Claude replies)
            placeholder = DiagramLoadingPlaceholder()
            self.message_layout.insertWidget(
                self.message_layout.count() - 1, placeholder
            )
            self._scroll_to_bottom()

            # 3. Text explanation (bullets + Read More) below the diagram
            self._add_ai_response(display_text)

            # 4. Kick off Claude diagram generation
            def on_ready(diagram_type, diagram_code):
                self._replace_widget(
                    placeholder, build_diagram_widget(diagram_type, diagram_code)
                )
                self._scroll_to_bottom()

            def on_error(message):
                err = QLabel(message)
                err.setObjectName("DiagramPlaceholder")
                err.setWordWrap(True)
                self._replace_widget(placeholder, err)
                self._scroll_to_bottom()

            self.claude_client.generate_diagram(diagram_description, on_ready, on_error)

        else:
            # No diagram — just show the text explanation
            self._add_ai_response(display_text)

    def _on_ollama_error(self, message: str):
        self._hide_typing_indicator()
        self._set_input_enabled(True)
        self._show_error(message)

    # ──────────────────────────────────────────────────────────────────
    # Widget helpers
    # ──────────────────────────────────────────────────────────────────
    def _add_user_bubble(self, text: str):
        """Right-aligned gold user bubble (FR-08)."""
        bubble = QLabel(text)
        bubble.setObjectName("UserBubble")
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(BUBBLE_MAX_WIDTH)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(bubble)

        row_widget = QWidget()
        row_widget.setLayout(row)
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
        self._scroll_to_bottom()

    def _add_ai_response(self, text: str):
        """Left-aligned AI response as bullets + Read More (FR-09)."""
        response_widget = AIResponseWidget(text)

        row = QHBoxLayout()
        row.addWidget(response_widget)
        row.addStretch(1)

        row_widget = QWidget()
        row_widget.setLayout(row)
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
        self._scroll_to_bottom()

    def _add_section_label(self, text: str):
        """Gold italic label above a diagram section."""
        label = QLabel(text)
        label.setObjectName("DiagramSectionLabel")
        self.message_layout.insertWidget(self.message_layout.count() - 1, label)

    def _replace_widget(self, old_widget: QWidget, new_widget: QWidget):
        """Swap the loading placeholder for the real diagram in-place."""
        index = self.message_layout.indexOf(old_widget)
        self.message_layout.insertWidget(index, new_widget)
        self.message_layout.removeWidget(old_widget)
        old_widget.deleteLater()

    def _scroll_to_bottom(self):
        """FR-12: defer scroll so the layout has time to update."""
        QTimer.singleShot(
            0,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ),
        )

    def _show_error(self, message: str):
        self.error_banner.setText(f"⚠ {message}")
        self.error_banner.show()

    def _hide_error(self):
        self.error_banner.hide()

    def clear_history(self):
        """Reset the conversation — remove all bubbles and Ollama history."""
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.ollama_client.clear_history()
        self._hide_error()
