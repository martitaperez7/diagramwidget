"""
ui/floating_window.py
----------------------
The main floating, always-on-top window for Diagram Tutor.
Redesigned with UMBC Whimsy Academia theme — black, gold, parchment.

Covers:
    FR-01: frameless panel, always on top
    FR-02: draggable by the title bar
    FR-03: resizable via bottom-right grip
    FR-04: minimize button collapses to title bar
    FR-05: launches bottom-right corner
    FR-06: no taskbar entry
    NFR-08: consistent UMBC dark theme
"""

import sys

from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
    QApplication,
)

from ui.styles import MAIN_STYLESHEET
from ui.chat_panel import ChatPanel

DEFAULT_WIDTH     = 400
DEFAULT_HEIGHT    = 600
MARGIN_FROM_EDGE  = 24
TITLEBAR_HEIGHT   = 44


class TitleBar(QWidget):
    """
    Custom UMBC-branded title bar.
    Shows the Retriever paw emoji + "Diagram Tutor · UMBC" in gold Georgia serif.
    Drag to move the window (FR-02). Hosts minimize + close buttons.
    """

    def __init__(self, parent_window):
        super().__init__(parent_window)

        # Store a reference to the FloatingWindow so we can call its methods
        self.parent_window = parent_window
        self.setObjectName("TitleBar")
        self.setFixedHeight(TITLEBAR_HEIGHT)

        # Used to track the mouse offset when dragging the window
        self._drag_offset = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)

        # ── Logo / branding ────────────────────────────────────────────
        logo = QLabel("🐾")
        logo.setStyleSheet(
            "font-size: 18px; background: transparent; border: none;"
        )
        layout.addWidget(logo)

        title = QLabel("Diagram Tutor")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        tag = QLabel("· UMBC")
        tag.setStyleSheet(
            "color: #7A5C00; font-family: Georgia, serif; "
            "font-size: 10px; font-style: italic; "
            "background: transparent; border: none;"
        )
        layout.addWidget(tag)

        layout.addStretch(1)

        # ── Minimize button ────────────────────────────────────────────
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setObjectName("TitleBarButton")
        self.minimize_btn.setFixedSize(26, 26)
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.clicked.connect(self.parent_window.toggle_minimize)
        layout.addWidget(self.minimize_btn)

        # ── Close button ───────────────────────────────────────────────
        # Connects to _on_close which calls sys.exit(0) so the terminal
        # returns the prompt immediately when the user clicks X.
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("TitleBarButton")
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self._on_close)
        layout.addWidget(self.close_btn)

    def _on_close(self):
        """
        Close the window AND force-quit the Python process.

        Why sys.exit(0) instead of just self.parent_window.close()?
        -----------------------------------------------------------
        self.parent_window.close() hides the window but keeps the
        Python process running in the background — that's why the
        terminal cursor disappears and you can't type.

        sys.exit(0) tells the OS to end the process completely,
        which returns control to the terminal immediately.
        0 = "exited cleanly, no errors."
        """
        self.parent_window.close()
        sys.exit(0)

    # ── Drag to move the window ────────────────────────────────────────
    # Since we removed the OS title bar (FramelessWindowHint), we
    # manually re-implement dragging using these two mouse events.

    def mousePressEvent(self, event):
        """Record where on the title bar the user clicked."""
        if event.button() == Qt.LeftButton:
            self._drag_offset = (
                event.globalPos() - self.parent_window.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        """Move the window to follow the mouse while dragging."""
        if event.buttons() == Qt.LeftButton:
            self.parent_window.move(event.globalPos() - self._drag_offset)
            event.accept()


class FloatingWindow(QWidget):
    """
    Top-level floating panel — UMBC Whimsy Academia edition.
    Contains TitleBar + ChatPanel + resize grip.
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("FloatingPanel")

        # Always on top, no OS frame, no taskbar entry
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        # False here means a solid (non-transparent) background —
        # keeps the window looking clean on all Windows versions
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Apply the full UMBC theme stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self._place_bottom_right()

        self._is_minimized    = False
        self._expanded_height = DEFAULT_HEIGHT

        self._build_ui()

    def _place_bottom_right(self):
        """Place the widget in the bottom-right corner of the screen (FR-05)."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width()  - self.width()  - MARGIN_FROM_EDGE
        y = screen.height() - self.height() - MARGIN_FROM_EDGE
        self.move(max(x, 0), max(y, 0))

    def _build_ui(self):
        """
        Assembles the layout:
          TitleBar
          ChatPanel  (stretches to fill space)
          Resize grip (bottom-right corner)
        """
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Custom title bar (drag + minimize + close)
        self.title_bar = TitleBar(self)
        outer.addWidget(self.title_bar)

        # Full chat panel (messages, diagram, input bar)
        self.chat_panel = ChatPanel(self)
        outer.addWidget(self.chat_panel, stretch=1)

        # Resize grip — pushed to bottom-right via addStretch
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 4, 4)
        grip_row.addStretch(1)
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet(
            "QSizeGrip { background: transparent; width: 12px; height: 12px; }"
        )
        grip_row.addWidget(
            self.size_grip, alignment=Qt.AlignBottom | Qt.AlignRight
        )
        outer.addLayout(grip_row)

    def toggle_minimize(self):
        """
        FR-04: Collapse the panel to just the title bar, or restore it.

        Minimized  → body hidden, height locked to TITLEBAR_HEIGHT
        Restored   → body visible, height freed back to previous size
        """
        if not self._is_minimized:
            self._expanded_height = self.height()
            self.chat_panel.hide()
            self.size_grip.hide()
            self.setFixedHeight(TITLEBAR_HEIGHT)
            self.title_bar.minimize_btn.setText("□")
            self.title_bar.minimize_btn.setToolTip("Restore")
        else:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.resize(self.width(), self._expanded_height)
            self.chat_panel.show()
            self.size_grip.show()
            self.title_bar.minimize_btn.setText("−")
            self.title_bar.minimize_btn.setToolTip("Minimize")
        self._is_minimized = not self._is_minimized

    def sizeHint(self):
        return QSize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
