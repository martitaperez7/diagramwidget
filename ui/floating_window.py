"""
ui/floating_window.py
----------------------
The main floating, always-on-top window for Diagram Tutor.

Covers these requirements from the spec:
    FR-01: frameless panel, always on top of all other windows
    FR-02: draggable by clicking and holding the title bar
    FR-03: resizable via a bottom-right corner grip
    FR-04: minimize button collapses panel to title bar only
    FR-05: launches in the bottom-right corner of the screen by default
    FR-06: does not appear in the OS taskbar
    NFR-08: consistent dark theme (via styles.MAIN_STYLESHEET)

Beginner notes:
    - PyQt5 windows are normally drawn by the OS with a title bar, min/max/
      close buttons, etc. Setting Qt.FramelessWindowHint removes all of that
      so we can draw our OWN title bar (see TitleBar class below) and have
      full control of how the window looks and behaves.
    - "Always on top" is done with Qt.WindowStaysOnTopHint.
    - "Don't show in taskbar" is done with Qt.Tool (Tool windows are treated
      by the OS as accessory windows, not full applications).
"""

from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
)

from ui.styles import MAIN_STYLESHEET
from ui.chat_panel import ChatPanel


# Default panel size used on first launch (FR-05: bottom-right corner).
DEFAULT_WIDTH = 380
DEFAULT_HEIGHT = 560
MARGIN_FROM_EDGE = 24
TITLEBAR_HEIGHT = 36


class TitleBar(QWidget):
    """
    Custom title bar that replaces the OS-drawn one.

    Clicking and dragging this widget moves the whole floating window
    (FR-02). It also hosts the minimize button (FR-04).
    """

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setObjectName("TitleBar")
        self.setFixedHeight(TITLEBAR_HEIGHT)

        # Track where on the title bar the mouse was pressed, so we can
        # compute how far to move the window as the mouse drags.
        self._drag_offset = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(4)

        self.title_label = QLabel("Diagram Tutor")
        self.title_label.setObjectName("TitleLabel")
        layout.addWidget(self.title_label)
        layout.addStretch(1)

        self.minimize_btn = QPushButton("−")  # minus sign
        self.minimize_btn.setObjectName("TitleBarButton")
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.setToolTip("Minimize to title bar")
        self.minimize_btn.clicked.connect(self.parent_window.toggle_minimize)
        layout.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("✕")  # multiplication X
        self.close_btn.setObjectName("TitleBarButton")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setToolTip("Close Diagram Tutor")
        self.close_btn.clicked.connect(self.parent_window.close)
        layout.addWidget(self.close_btn)

    # -- Drag-to-move handlers -------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Remember the offset between the mouse and the window's
            # top-left corner so dragging feels natural (no "jump").
            self._drag_offset = (
                event.globalPos() - self.parent_window.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.parent_window.move(event.globalPos() - self._drag_offset)
            event.accept()


class FloatingWindow(QWidget):
    """
    The top-level floating panel. Contains the custom TitleBar and the
    ChatPanel (chat bubbles + input box + diagram area).
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("FloatingPanel")

        # --- Window flags: frameless, always-on-top, no taskbar entry ---
        # FR-01 + FR-06: frameless (Qt.FramelessWindowHint) and hidden from
        # the taskbar (Qt.Tool). FR-01 also requires staying on top of
        # every other window (Qt.WindowStaysOnTopHint).
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        # A translucent background lets us draw rounded corners in QSS
        # instead of a harsh rectangular window.
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.setStyleSheet(MAIN_STYLESHEET)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self._place_bottom_right()  # FR-05

        self._is_minimized = False
        self._expanded_height = DEFAULT_HEIGHT

        self._build_ui()

    # ------------------------------------------------------------------
    def _place_bottom_right(self):
        """FR-05: launch in the bottom-right corner of the primary screen."""
        from PyQt5.QtWidgets import QApplication

        screen_geom = QApplication.primaryScreen().availableGeometry()
        x = screen_geom.width() - self.width() - MARGIN_FROM_EDGE
        y = screen_geom.height() - self.height() - MARGIN_FROM_EDGE
        self.move(max(x, 0), max(y, 0))

    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        outer_layout.addWidget(self.title_bar)

        # The chat panel holds everything below the title bar: message
        # bubbles, diagram area, typing indicator, and the input row.
        self.chat_panel = ChatPanel(self)
        outer_layout.addWidget(self.chat_panel, stretch=1)

        # FR-03: resize grip in the bottom-right corner.
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 0, 0)
        grip_row.addStretch(1)
        self.size_grip = QSizeGrip(self)
        grip_row.addWidget(self.size_grip, alignment=Qt.AlignBottom | Qt.AlignRight)
        outer_layout.addLayout(grip_row)

    # ------------------------------------------------------------------
    def toggle_minimize(self):
        """
        FR-04: collapse the panel down to just the title bar, and restore
        it back to full size on a second click.
        """
        if not self._is_minimized:
            self._expanded_height = self.height()
            self.chat_panel.hide()
            self.size_grip.hide()
            self.setFixedHeight(TITLEBAR_HEIGHT)
            self.title_bar.minimize_btn.setText("□")  # restore icon
            self.title_bar.minimize_btn.setToolTip("Restore")
        else:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)  # Qt's "no maximum" sentinel
            self.resize(self.width(), self._expanded_height)
            self.chat_panel.show()
            self.size_grip.show()
            self.title_bar.minimize_btn.setText("−")
            self.title_bar.minimize_btn.setToolTip("Minimize to title bar")
        self._is_minimized = not self._is_minimized

    def sizeHint(self):
        return QSize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
