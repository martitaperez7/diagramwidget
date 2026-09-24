# ui/styles.py
# =============================================================
# UMBC Whimsy Academia Theme — Diagram Tutor
# =============================================================
#
# Palette:
#   UMBC Black   #0D0D0D  — deep background
#   UMBC Gold    #F0B400  — primary accent, titles, highlights
#   Parchment    #FAF3DC  — warm off-white for AI text (feels academic)
#   Charcoal     #1C1C1C  — panel / bubble backgrounds
#   Slate        #2A2A2A  — input field background
#   Dim Gold     #7A5C00  — muted gold for secondary text
#   White        #FFFFFF  — user bubble text
#   Error Red    #C0392B  — error banner
#
# Whimsy touches:
#   - Gold border accent on the title bar
#   - Slightly rounded corners everywhere (8-12px)
#   - Parchment-toned AI bubbles (like aged paper)
#   - Gold send button
#   - Italic placeholder text
# =============================================================

MAIN_STYLESHEET = """

/* ── Root panel ──────────────────────────────────────────── */
QWidget#FloatingPanel {
    background-color: #0D0D0D;
    border: 1px solid #F0B400;
    border-radius: 12px;
}

/* ── Title bar ───────────────────────────────────────────── */
QWidget#TitleBar {
    background-color: #0D0D0D;
    border-bottom: 2px solid #F0B400;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

QLabel#TitleLabel {
    color: #F0B400;
    font-family: Georgia, serif;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 1px;
}

/* ── Title bar buttons (minimize / close) ────────────────── */
QPushButton#TitleBarButton {
    background-color: transparent;
    color: #F0B400;
    border: 1px solid #7A5C00;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}
QPushButton#TitleBarButton:hover {
    background-color: #F0B400;
    color: #0D0D0D;
}
QPushButton#TitleBarButton:pressed {
    background-color: #C49200;
}

/* ── Scroll area + chat container ────────────────────────── */
QScrollArea#ChatScrollArea {
    background-color: #0D0D0D;
    border: none;
}
QWidget#ChatContainer {
    background-color: #0D0D0D;
}

/* ── Scrollbar ───────────────────────────────────────────── */
QScrollBar:vertical {
    background: #1C1C1C;
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #F0B400;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── AI message bubble (parchment / aged paper) ──────────── */
/* Targets QWidget now — the whole bubble box, not individual labels */
QWidget#AIBubble {
    background-color: #1E1A0E;
    border: 1px solid #7A5C00;
    border-radius: 10px;
    border-top-left-radius: 2px;
}

/* ── User message bubble ─────────────────────────────────── */
QLabel#UserBubble {
    background-color: #F0B400;
    color: #0D0D0D;
    border-radius: 10px;
    border-bottom-right-radius: 2px;
    padding: 10px 12px;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
    font-weight: 600;
}

/* ── Typing indicator ────────────────────────────────────── */
QLabel#TypingIndicator {
    color: #7A5C00;
    font-family: Georgia, serif;
    font-style: italic;
    font-size: 11px;
    padding: 4px 8px;
}

/* ── Diagram section label ───────────────────────────────── */
QLabel#DiagramSectionLabel {
    color: #F0B400;
    font-family: Georgia, serif;
    font-size: 11px;
    font-style: italic;
    letter-spacing: 0.5px;
    padding: 6px 0px 2px 2px;
}

/* ── Diagram loading placeholder ─────────────────────────── */
QLabel#DiagramPlaceholder {
    background-color: #1C1C1C;
    color: #7A5C00;
    border: 1px dashed #7A5C00;
    border-radius: 8px;
    padding: 10px 16px;
    font-family: Georgia, serif;
    font-style: italic;
    font-size: 11px;
    min-height: 40px;
    max-height: 60px;
}

/* ── Read more button ────────────────────────────────────── */
QPushButton#ReadMoreButton {
    background-color: transparent;
    color: #F0B400;
    border: 1px solid #7A5C00;
    border-radius: 6px;
    padding: 3px 10px;
    font-family: Georgia, serif;
    font-style: italic;
    font-size: 11px;
    text-align: left;
}
QPushButton#ReadMoreButton:hover {
    background-color: #1E1A0E;
    border-color: #F0B400;
}

/* ── Input field ─────────────────────────────────────────── */
QLineEdit#MessageInput {
    background-color: #1C1C1C;
    color: #FAF3DC;
    border: 1px solid #7A5C00;
    border-radius: 8px;
    padding: 7px 12px;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
    selection-background-color: #F0B400;
    selection-color: #0D0D0D;
}
QLineEdit#MessageInput:focus {
    border: 1px solid #F0B400;
}
QLineEdit#MessageInput::placeholder {
    color: #555555;
    font-style: italic;
}
QLineEdit#MessageInput:disabled {
    color: #444444;
    border-color: #333333;
}

/* ── Send button ─────────────────────────────────────────── */
QPushButton#SendButton {
    background-color: #F0B400;
    color: #0D0D0D;
    border: none;
    border-radius: 8px;
    padding: 7px 16px;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
    font-weight: bold;
}
QPushButton#SendButton:hover {
    background-color: #FFD000;
}
QPushButton#SendButton:pressed {
    background-color: #C49200;
}
QPushButton#SendButton:disabled {
    background-color: #3A3000;
    color: #666600;
}

/* ── Error banner ────────────────────────────────────────── */
QLabel#ErrorBanner {
    background-color: #2A0A0A;
    color: #E74C3C;
    border: 1px solid #C0392B;
    border-radius: 6px;
    padding: 6px 10px;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
    margin: 0px 10px;
}

"""
