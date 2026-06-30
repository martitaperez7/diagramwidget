"""
ui/chat_panel.py
------------------
The chat area: message bubbles, typing indicator, diagram area, and the
input row (text field + send button).

Covers:
    FR-07: submit via Enter key or send button
    FR-08: user messages as right-aligned blue bubbles
    FR-09: AI responses as left-aligned grey bubbles
    FR-10: animated typing indicator while AI is generating
    FR-11: input field + send button disabled while a response is pending
    FR-12: auto-scroll to latest message after each new response
    FR-13: text in message bubbles is selectable/copyable
    FR-19/FR-21/FR-22: trigger Claude diagram generation, show a loading
        placeholder, then render the finished diagram below the AI reply
    NFR-06: plain-language errors with a suggested fix, shown as a banner

Beginner notes:
    - A QScrollArea + a vertically-stacked QVBoxLayout inside it is the
      standard PyQt5 pattern for a scrolling chat feed: each new bubble is
      just another widget added to that vertical layout.
    - QLabel with setTextInteractionFlags(Qt.TextSelectableByMouse) is what
      makes bubble text highlightable/copyable (FR-13) without making the
      label editable.
"""

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

BUBBLE_MAX_WIDTH = 260


class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ollama_client = OllamaClient()
        self.claude_client = ClaudeClient()

        self._typing_label = None
        self._typing_timer = None
        self._typing_dot_count = 0

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Scrollable message feed -------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ChatScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.message_container = QWidget()
        self.message_container.setObjectName("ChatContainer")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(10, 10, 10, 10)
        self.message_layout.setSpacing(10)
        self.message_layout.addStretch(1)  # keeps bubbles pinned to the top

        self.scroll_area.setWidget(self.message_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # --- Error banner (hidden until needed) ---------------------------
        self.error_banner = QLabel("")
        self.error_banner.setObjectName("ErrorBanner")
        self.error_banner.setWordWrap(True)
        self.error_banner.hide()
        layout.addWidget(self.error_banner)

        # --- Input row: text field + send button --------------------------
        input_row = QHBoxLayout()
        input_row.setContentsMargins(10, 8, 10, 10)
        input_row.setSpacing(8)

        self.message_input = QLineEdit()
        self.message_input.setObjectName("MessageInput")
        self.message_input.setPlaceholderText("Ask about any topic...")
        self.message_input.returnPressed.connect(self._on_send_clicked)  # FR-07
        input_row.addWidget(self.message_input, stretch=1)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("SendButton")
        self.send_button.clicked.connect(self._on_send_clicked)  # FR-07
        input_row.addWidget(self.send_button)

        layout.addLayout(input_row)

    # ------------------------------------------------------------------
    # Sending a message
    # ------------------------------------------------------------------
    def _on_send_clicked(self):
        text = self.message_input.text().strip()
        if not text:
            return

        self._add_bubble(text, is_user=True)  # FR-08
        self.message_input.clear()
        self._set_input_enabled(False)  # FR-11
        self._hide_error()
        self._show_typing_indicator()  # FR-10

        self.ollama_client.send_message(
            text,
            on_response=self._on_ollama_response,
            on_error=self._on_ollama_error,
        )

    def _set_input_enabled(self, enabled: bool):
        """FR-11: disable input + send button while a response is pending."""
        self.message_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        if enabled:
            self.message_input.setFocus()

    # ------------------------------------------------------------------
    # Typing indicator (FR-10)
    # ------------------------------------------------------------------
    def _show_typing_indicator(self):
        self._typing_label = QLabel("AI is thinking")
        self._typing_label.setObjectName("TypingIndicator")
        self.message_layout.insertWidget(
            self.message_layout.count() - 1, self._typing_label
        )

        self._typing_dot_count = 0
        self._typing_timer = QTimer(self)
        self._typing_timer.timeout.connect(self._animate_typing_dots)
        self._typing_timer.start(400)  # animate every 400ms
        self._scroll_to_bottom()

    def _animate_typing_dots(self):
        self._typing_dot_count = (self._typing_dot_count + 1) % 4
        dots = "." * self._typing_dot_count
        if self._typing_label is not None:
            self._typing_label.setText(f"AI is thinking{dots}")

    def _hide_typing_indicator(self):
        if self._typing_timer is not None:
            self._typing_timer.stop()
            self._typing_timer = None
        if self._typing_label is not None:
            self._typing_label.deleteLater()
            self._typing_label = None

    # ------------------------------------------------------------------
    # Ollama response handling
    # ------------------------------------------------------------------
    def _on_ollama_response(self, display_text, diagram_description):
        self._hide_typing_indicator()
        self._add_bubble(display_text, is_user=False)  # FR-09
        self._set_input_enabled(True)

        if diagram_description:
            self._request_diagram(diagram_description)  # FR-19

    def _on_ollama_error(self, message):
        self._hide_typing_indicator()
        self._set_input_enabled(True)
        self._show_error(message)  # NFR-06 / NFR-09

    # ------------------------------------------------------------------
    # Claude diagram generation (FR-19..22)
    # ------------------------------------------------------------------
    def _request_diagram(self, description: str):
        placeholder = DiagramLoadingPlaceholder()  # FR-22
        self.message_layout.insertWidget(self.message_layout.count() - 1, placeholder)
        self._scroll_to_bottom()

        def on_ready(diagram_type, diagram_code):
            self._replace_widget(placeholder, build_diagram_widget(diagram_type, diagram_code))
            self._scroll_to_bottom()

        def on_error(message):
            error_label = QLabel(message)
            error_label.setObjectName("DiagramPlaceholder")
            error_label.setWordWrap(True)
            self._replace_widget(placeholder, error_label)  # NFR-10 fallback
            self._scroll_to_bottom()

        self.claude_client.generate_diagram(description, on_ready, on_error)

    def _replace_widget(self, old_widget, new_widget):
        """Swaps the loading placeholder for the real diagram/error widget
        in-place, preserving its position in the chat feed."""
        index = self.message_layout.indexOf(old_widget)
        self.message_layout.insertWidget(index, new_widget)
        self.message_layout.removeWidget(old_widget)
        old_widget.deleteLater()

    # ------------------------------------------------------------------
    # Bubble / scrolling / error-banner helpers
    # ------------------------------------------------------------------
    def _add_bubble(self, text: str, is_user: bool):
        bubble = QLabel(text)
        bubble.setObjectName("UserBubble" if is_user else "AIBubble")
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(BUBBLE_MAX_WIDTH)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)  # FR-13
        bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        row = QHBoxLayout()
        if is_user:
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)

        row_widget = QWidget()
        row_widget.setLayout(row)
        self.message_layout.insertWidget(self.message_layout.count() - 1, row_widget)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """FR-12: auto-scroll to the latest message. The scrollbar's range
        isn't updated until after the layout pass, so we defer the actual
        scroll to the next event-loop tick."""
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

    # ------------------------------------------------------------------
    # Step 6 feature referenced in the team checklist: clear_history()
    # ------------------------------------------------------------------
    def clear_history(self):
        """Removes all bubbles/diagrams and resets the Ollama conversation
        so the user can start a fresh topic."""
        while self.message_layout.count() > 1:  # keep the trailing stretch
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.ollama_client.clear_history()
        self._hide_error()
