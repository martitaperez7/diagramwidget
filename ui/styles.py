"""
ui/styles.py
-------------
Centralized dark-theme styling for the whole app (NFR-08: consistent dark
theme everywhere) plus hover/focus states for every interactive element
(NFR-07).

Keeping all colors and QSS (Qt's CSS-like styling language) in ONE file
means that if we ever want to re-theme the app, we only have to edit this
file instead of hunting through every widget.
"""

# ---------------------------------------------------------------------------
# Color palette - change these values to re-theme the entire app.
# ---------------------------------------------------------------------------
COLOR_BG_PANEL = "#1e1f26"          # main panel background
COLOR_BG_TITLEBAR = "#15161b"       # title bar background
COLOR_BG_CHAT = "#23242c"           # chat scroll area background
COLOR_BUBBLE_USER = "#3b82f6"       # right-aligned user bubble (blue, FR-08)
COLOR_BUBBLE_AI = "#3a3b44"         # left-aligned AI bubble (grey, FR-09)
COLOR_TEXT_PRIMARY = "#f5f5f7"
COLOR_TEXT_SECONDARY = "#a0a0ab"
COLOR_BORDER = "#33343d"
COLOR_ACCENT = "#3b82f6"
COLOR_ACCENT_HOVER = "#5a93f7"
COLOR_ERROR = "#e35d6a"
COLOR_INPUT_BG = "#2a2b33"


# ---------------------------------------------------------------------------
# Master stylesheet applied to the whole floating panel (QSS).
# ---------------------------------------------------------------------------
MAIN_STYLESHEET = f"""
QWidget#FloatingPanel {{
    background-color: {COLOR_BG_PANEL};
    border-radius: 10px;
}}

QWidget#TitleBar {{
    background-color: {COLOR_BG_TITLEBAR};
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}}

QLabel#TitleLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-weight: 600;
    font-size: 13px;
    padding-left: 8px;
}}

QPushButton#TitleBarButton {{
    background-color: transparent;
    color: {COLOR_TEXT_SECONDARY};
    border: none;
    font-size: 14px;
    border-radius: 4px;
}}

QPushButton#TitleBarButton:hover {{
    background-color: {COLOR_BORDER};
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton#TitleBarButton:focus {{
    outline: 2px solid {COLOR_ACCENT};
}}

QScrollArea#ChatScrollArea, QWidget#ChatContainer {{
    background-color: {COLOR_BG_CHAT};
    border: none;
}}

QLabel#UserBubble {{
    background-color: {COLOR_BUBBLE_USER};
    color: white;
    border-radius: 12px;
    padding: 8px 12px;
}}

QLabel#AIBubble {{
    background-color: {COLOR_BUBBLE_AI};
    color: {COLOR_TEXT_PRIMARY};
    border-radius: 12px;
    padding: 8px 12px;
}}

QLabel#TypingIndicator {{
    color: {COLOR_TEXT_SECONDARY};
    font-style: italic;
    padding: 4px 12px;
}}

QLineEdit#MessageInput {{
    background-color: {COLOR_INPUT_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
}}

QLineEdit#MessageInput:focus {{
    border: 1px solid {COLOR_ACCENT};
}}

QLineEdit#MessageInput:disabled {{
    color: {COLOR_TEXT_SECONDARY};
    background-color: {COLOR_BG_PANEL};
}}

QPushButton#SendButton {{
    background-color: {COLOR_ACCENT};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}}

QPushButton#SendButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#SendButton:disabled {{
    background-color: {COLOR_BORDER};
    color: {COLOR_TEXT_SECONDARY};
}}

QLabel#ErrorBanner {{
    background-color: rgba(227, 93, 106, 0.15);
    color: {COLOR_ERROR};
    border: 1px solid {COLOR_ERROR};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}}

QLabel#DiagramPlaceholder {{
    background-color: {COLOR_BG_CHAT};
    color: {COLOR_TEXT_SECONDARY};
    border: 1px dashed {COLOR_BORDER};
    border-radius: 8px;
    padding: 16px;
    font-style: italic;
}}

QScrollBar:vertical {{
    background: {COLOR_BG_CHAT};
    width: 10px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: 5px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLOR_ACCENT};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QSizeGrip {{
    background-color: transparent;
    width: 16px;
    height: 16px;
}}
"""
