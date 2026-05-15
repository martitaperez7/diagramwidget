# ============================================================
# ui/floating_window.py — The floating window shell
# ============================================================
#
# WHAT IS THIS FILE?
# ------------------
# This file is responsible for the WINDOW itself — the outer
# shell that floats on top of everything on the user's screen.
#
# Think of it like a picture frame:
#   floating_window.py  = the FRAME  (shape, position, controls)
#   chat_panel.py       = the PICTURE inside the frame (messages)
#
# This file handles:
#   - Making the window always stay on top of other windows
#   - Removing the default OS title bar so we can draw our own
#   - The custom title bar (brain icon, app name, buttons)
#   - Dragging the window by clicking the title bar
#   - Resizing the window by dragging the bottom-right corner
#   - Minimising to just the title bar
#   - The text input bar at the bottom
#   - All CSS styling for the window shell
#
# WHAT CHANGED FROM STEP 1?
# -------------------------
# In Step 1 everything was in this one file.
# In Step 2 we extracted all chat logic into chat_panel.py.
# This file now imports ChatPanel and places it in the body.
# This keeps the code organised and easy to maintain.
#
# ============================================================


# ── Imports ───────────────────────────────────────────────────
#
# We only import the PyQt5 components we actually use in this file.
# Chat-related components (QScrollArea, QFrame, etc.) are now
# imported in chat_panel.py instead.

from PyQt5.QtWidgets import (
    # QWidget — base class for all UI elements; our window inherits it
    QWidget,

    # QVBoxLayout — stacks widgets vertically (top to bottom)
    QVBoxLayout,

    # QHBoxLayout — arranges widgets horizontally (left to right)
    QHBoxLayout,

    # QLabel — displays text (used for the brain icon and app title)
    QLabel,

    # QPushButton — a clickable button (minimize and close buttons)
    QPushButton,

    # QSizeGrip — the built-in resize handle for the bottom-right corner
    QSizeGrip,

    # QLineEdit — a single-line text input field (the message input bar)
    QLineEdit,

    # QScrollArea — imported here in case it's needed for the shell;
    # primary usage is in chat_panel.py
    QScrollArea,
)

from PyQt5.QtCore import (
    # Qt — namespace of constants (Qt.LeftButton, Qt.Tool, etc.)
    Qt,

    # QPoint — stores an (x, y) coordinate pair.
    # Used to track the mouse position during window dragging.
    QPoint,

    # QTimer — fires a function after a delay.
    # Used here to simulate AI response delay in _on_send().
    QTimer,
)

from PyQt5.QtGui import (
    # QFont — sets font family and size on widgets
    QFont,
)

# Import our ChatPanel class from the other file in the ui/ folder.
# This is a RELATIVE import — "from ui.chat_panel" means
# "look in the ui folder for a file called chat_panel.py
# and import the ChatPanel class from it."
from ui.chat_panel import ChatPanel


# ── The FloatingWindow Class ───────────────────────────────────
#
# FloatingWindow inherits from QWidget.
# This means it IS a QWidget — it gets all of QWidget's built-in
# behaviour (painting, events, layouts) and we add our own on top.
#
class FloatingWindow(QWidget):

    def __init__(self):
        """
        Constructor — runs when FloatingWindow() is called in main.py.

        Sets up all window-level behaviour:
          - Window flags (always on top, frameless, no taskbar entry)
          - Transparent background (for rounded corners)
          - Starting size and position
          - State variables for dragging and minimising
          - Builds the UI and applies styles
        """

        # Call QWidget's constructor first so it initialises itself.
        # Every class that inherits from another MUST call super().__init__()
        # before doing anything else.
        super().__init__()

        # ── Window Flags ──────────────────────────────────────
        #
        # setWindowFlags() tells the operating system how to treat
        # this window. We combine flags with | (the "or" operator).
        #
        # Qt.WindowStaysOnTopHint
        #   Forces this window to always appear in FRONT of all others.
        #   Even when the user clicks on Chrome, our panel stays visible.
        #   This is the core feature that makes it a "floating widget."
        #
        # Qt.FramelessWindowHint
        #   Removes the OS-drawn window frame entirely: no title bar,
        #   no border, no default minimize/maximize/close buttons.
        #   We do this so we can draw our OWN title bar that perfectly
        #   matches our dark theme design.
        #
        # Qt.Tool
        #   Classifies this as a "tool window." The main effect is
        #   it does NOT appear as a separate button in the taskbar,
        #   keeping the user's taskbar clean while the app is open.
        #
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint  |
            Qt.Tool
        )

        # ── Transparent background ────────────────────────────
        #
        # Qt.WA_TranslucentBackground is a "widget attribute" that
        # enables per-pixel transparency on this window.
        #
        # Why do we need this?
        # Our container widget has border-radius: 16px in its CSS,
        # which rounds the corners. But corners are square by nature.
        # With WA_TranslucentBackground, the "cut off" corner pixels
        # become truly transparent (you see through to the desktop).
        # Without it, those corner pixels would be white or grey —
        # giving the widget ugly white square corners.
        #
        self.setAttribute(Qt.WA_TranslucentBackground)

        # ── Starting size ─────────────────────────────────────
        #
        # resize(width, height) sets the initial window size.
        # The user can change this by dragging the resize grip.
        # 380px wide, 580px tall is a comfortable chat panel size.
        self.resize(380, 580)

        # ── Starting position ─────────────────────────────────
        #
        # Place the window in the bottom-right corner of the screen.
        # This is where users expect floating chat helpers to appear
        # (think of the chat bubbles on websites).
        self._place_bottom_right()

        # ── State variables ───────────────────────────────────
        #
        # These three variables track things that change while
        # the app is running. By storing them on self (the instance),
        # they're accessible in ALL methods of this class.

        # _drag_pos: Stores WHERE on the title bar the user clicked
        #            when starting to drag. QPoint() = (0, 0) = "not set yet."
        self._drag_pos = QPoint()

        # _is_dragging: True while the user is actively dragging
        #               the window. False otherwise.
        self._is_dragging = False

        # _is_minimized: True when the panel is collapsed to just
        #                the title bar. False when fully open.
        self._is_minimized = False

        # ── Build and style ───────────────────────────────────
        #
        # _build_ui() creates all the visual components.
        # _apply_styles() applies all the CSS styling to them.
        # They're separate so each has one clear job.
        self._build_ui()
        self._apply_styles()


    # ═══════════════════════════════════════════════════════════
    # SECTION 1: PLACEMENT
    # ═══════════════════════════════════════════════════════════

    def _place_bottom_right(self):
        """
        Moves the window to the bottom-right corner of the screen,
        with a 20-pixel gap from the right edge and bottom edge.

        Uses QDesktopWidget to get the screen dimensions, then
        calculates the correct (x, y) position for the top-left
        corner of our window.

        Screen coordinate system:
          (0, 0) = top-left corner of the screen
          (width, height) = bottom-right corner of the screen
          x increases going RIGHT
          y increases going DOWN
        """

        # QDesktopWidget provides information about the user's screen(s).
        # We import it here (locally) because it's only used in this method.
        from PyQt5.QtWidgets import QDesktopWidget

        # availableGeometry() returns a rectangle representing the
        # usable screen area — this EXCLUDES the taskbar/dock.
        # So if the taskbar is 40px tall, the available height is
        # screen_height - 40. This prevents our window sitting
        # behind the taskbar.
        screen = QDesktopWidget().availableGeometry()

        # Calculate x position (horizontal):
        # Start at the right edge (screen.width()),
        # go LEFT by our window width (self.width()),
        # then go LEFT 20 more pixels for the margin gap.
        x = screen.width() - self.width() - 20

        # Calculate y position (vertical):
        # Start at the bottom edge (screen.height()),
        # go UP by our window height (self.height()),
        # then go UP 20 more pixels for the margin gap.
        y = screen.height() - self.height() - 20

        # Move the window's top-left corner to (x, y).
        self.move(x, y)


    # ═══════════════════════════════════════════════════════════
    # SECTION 2: UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════

    def _build_ui(self):
        """
        Assembles all the visual components of the floating panel.

        Window layout (from top to bottom):
        ┌───────────────────────────────┐
        │  container (dark rounded card) │
        │  ┌─────────────────────────┐  │
        │  │  title_bar              │  │ ← 🧠 icon + title + buttons
        │  ├─────────────────────────┤  │
        │  │  body                   │  │
        │  │  ┌───────────────────┐  │  │
        │  │  │  chat_panel       │  │  │ ← all chat messages
        │  │  ├───────────────────┤  │  │
        │  │  │  input_row        │  │  │ ← text field + send button
        │  │  └───────────────────┘  │  │
        │  ├─────────────────────────┤  │
        │  │                  [grip] │  │ ← resize handle corner
        │  └─────────────────────────┘  │
        └───────────────────────────────┘
        """

        # ── Outermost layout ──────────────────────────────────
        #
        # This layout belongs to the FloatingWindow widget itself.
        # It holds a single child: the container card.
        outer = QVBoxLayout(self)  # 'self' = attach to FloatingWindow
        outer.setContentsMargins(0, 0, 0, 0)  # No outer padding
        outer.setSpacing(0)

        # ── Container widget ──────────────────────────────────
        #
        # This is the visible dark rounded card.
        # We give it an objectName "container" so CSS can target it
        # with QWidget#container { background-color: ... }
        self.container = QWidget()
        self.container.setObjectName("container")

        # The container has its own vertical layout for its children
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # ── Title bar ─────────────────────────────────────────
        #
        # _build_title_bar() creates and returns the title bar widget.
        # We store it as self.title_bar so the mouse drag methods
        # can check "did the user click inside the title bar?"
        self.title_bar = self._build_title_bar()
        c_layout.addWidget(self.title_bar)

        # ── Body ──────────────────────────────────────────────
        #
        # The body contains the chat panel and input row.
        # We store it as self.body so _toggle_minimize() can
        # hide/show the entire body at once.
        self.body = QWidget()
        self.body.setObjectName("body")

        b_layout = QVBoxLayout(self.body)
        b_layout.setContentsMargins(10, 8, 10, 8)  # Padding inside the body
        b_layout.setSpacing(8)  # Gap between chat panel and input row

        # ── Chat panel ────────────────────────────────────────
        #
        # ChatPanel is our custom class from chat_panel.py.
        # It handles all message bubbles, typing indicator, and diagrams.
        # We store it as self.chat_panel so _on_send() can call
        # methods like add_user_message() and show_typing() on it.
        self.chat_panel = ChatPanel()
        b_layout.addWidget(self.chat_panel)

        # ── Input row ─────────────────────────────────────────
        #
        # _build_input_row() returns the text field + send button widget.
        self.input_row = self._build_input_row()
        b_layout.addWidget(self.input_row)

        c_layout.addWidget(self.body)

        # ── Resize grip ───────────────────────────────────────
        #
        # QSizeGrip is a built-in PyQt5 widget — a small triangle
        # in the corner that the user can drag to resize the window.
        #
        # We place it in a QHBoxLayout with addStretch() before it,
        # which pushes the grip all the way to the RIGHT side.
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 4, 4)  # Small bottom-right margin
        grip_row.addStretch()  # Pushes grip to the right

        self.size_grip = QSizeGrip(self)
        self.size_grip.setObjectName("sizeGrip")
        grip_row.addWidget(self.size_grip)

        # addLayout() adds a layout (not a widget) to another layout.
        # We can't use addWidget() for layouts — that's only for widgets.
        c_layout.addLayout(grip_row)

        # Finally, add the fully-built container to the outer layout.
        outer.addWidget(self.container)


    def _build_title_bar(self):
        """
        Builds and returns the custom title bar widget.

        Since we removed the OS title bar with FramelessWindowHint,
        we create our own. It contains:
          Left side:  🧠 brain emoji icon + "Study Assistant" text
          Right side: ─ minimize button + ✕ close button

        The title bar is also our DRAG HANDLE — the mousePressEvent
        method checks if clicks land inside this widget before
        starting a drag.

        Returns:
            QWidget: The assembled title bar widget.
        """

        # A plain QWidget acts as the title bar container
        bar = QWidget()
        bar.setObjectName("titleBar")  # CSS target: QWidget#titleBar

        # Fixed height of 46px — consistent with typical title bars
        bar.setFixedHeight(46)

        # Horizontal layout: [icon] [title] [stretch] [minimize] [close]
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 10, 0)  # 14px left, 10px right padding
        layout.setSpacing(8)  # 8px between each element

        # ── Left side: icon + title ───────────────────────────

        # Brain emoji label
        icon = QLabel("🧠")
        # Use emoji-compatible font at size 16 for proper rendering
        icon.setFont(QFont("Segoe UI Emoji", 16))

        # App name label
        title = QLabel("Study Assistant")
        title.setObjectName("titleLabel")  # Styled in CSS

        layout.addWidget(icon)
        layout.addWidget(title)

        # addStretch() pushes everything after it to the RIGHT.
        # Without this, the buttons would be squished next to the title.
        layout.addStretch()

        # ── Right side: control buttons ───────────────────────
        #
        # _make_control_btn() is a helper that creates a small
        # circular button. We pass: the symbol, the colour, and
        # what function to call when clicked.

        # Yellow minimize button — collapses body to title bar only
        self.minimize_btn = self._make_control_btn(
            symbol="─",            # The dash symbol shown on the button
            color="#F0C040",       # Yellow colour
            callback=self._toggle_minimize  # Function called on click
        )

        # Red close button — closes and quits the app
        self.close_btn = self._make_control_btn(
            symbol="✕",            # The X symbol
            color="#FF6058",       # Red colour
            callback=self.close    # self.close() is a built-in QWidget method
        )

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.close_btn)

        return bar


    def _make_control_btn(self, symbol, color, callback):
        """
        A reusable helper that creates a small circular control button.

        Instead of writing the same button code twice (once for minimize,
        once for close), we put the shared code here and call it twice
        with different arguments.

        This follows the DRY principle: "Don't Repeat Yourself."

        Args:
            symbol   (str):      The character shown on the button (─ or ✕).
            color    (str):      Hex colour code for the button (#F0C040, #FF6058).
            callback (callable): The function to call when the button is clicked.

        Returns:
            QPushButton: A styled 22×22 circular button.
        """

        btn = QPushButton(symbol)

        # setFixedSize(22, 22) makes it a 22×22 pixel square.
        # Combined with border-radius: 11px in the CSS (half of 22),
        # the square becomes a perfect circle.
        btn.setFixedSize(22, 22)
        btn.setObjectName("controlBtn")

        # Apply CSS directly to this button using an f-string.
        # The f"..." syntax lets us insert Python variables into strings.
        # {color} is replaced with the actual hex value passed in.
        #
        # In PyQt5 style sheets, { and } are literal curly braces used
        # in CSS rules. But since we're inside an f-string, Python would
        # try to interpret { as a variable placeholder. To stop that,
        # we DOUBLE the curly braces: {{ and }} → output a literal { and }.
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};   /* the colour passed in */
                border: none;
                border-radius: 11px;         /* half of 22px = perfect circle */
                color: rgba(0,0,0,0.6);      /* semi-transparent symbol colour */
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: rgba(0,0,0,0.9);      /* darker symbol when hovered */
            }}
        """)

        # .clicked is a Qt "signal" — an event object that fires when
        # the button is clicked. .connect(callback) registers our
        # function to be called every time the signal fires.
        #
        # Signals and slots are how PyQt5 handles events:
        #   signal  = "something happened" (button clicked, timer fired, etc.)
        #   slot    = the function that responds to it
        #   connect = links the signal to the slot
        btn.clicked.connect(callback)

        return btn


    def _build_input_row(self):
        """
        Builds and returns the message input bar at the bottom.

        Contains:
          - A QLineEdit: single-line text field for typing messages
          - A send button (→): clicks to send the message

        Both the Enter key (via returnPressed signal) and the
        button click trigger _on_send().

        Returns:
            QWidget: The input row container widget.
        """

        # Container widget for the whole input row
        row = QWidget()
        row.setObjectName("inputRow")

        # Horizontal layout: [text field ─────────────────] [→]
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 4, 0, 0)  # 4px top padding only
        layout.setSpacing(8)  # 8px gap between field and button

        # ── Text input field ──────────────────────────────────
        #
        # QLineEdit is a single-line text entry widget.
        # (For multi-line, we'd use QTextEdit — that comes in a later step.)
        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")

        # Placeholder text — the dim hint shown when the field is empty.
        # Disappears as soon as the user starts typing.
        self.input_field.setPlaceholderText("Ask anything to learn visually...")

        # Fixed height keeps it consistent regardless of font size changes
        self.input_field.setFixedHeight(40)

        # returnPressed is a signal that fires when the user presses Enter.
        # We connect it to _on_send so Enter key = send message.
        # This is the same as pressing the → button.
        self.input_field.returnPressed.connect(self._on_send)

        # ── Send button ───────────────────────────────────────
        self.send_btn = QPushButton("→")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedSize(40, 40)  # Same height as input field
        self.send_btn.clicked.connect(self._on_send)

        layout.addWidget(self.input_field)
        layout.addWidget(self.send_btn)

        return row


    # ═══════════════════════════════════════════════════════════
    # SECTION 3: ACTIONS
    # What happens when the user interacts with the window
    # ═══════════════════════════════════════════════════════════

    def _toggle_minimize(self):
        """
        Toggles the panel between EXPANDED and MINIMIZED states.

        EXPANDED (normal):
          - Body is visible (chat + input bar shown)
          - Window height is free to resize (starts at 580px)
          - Minimize button shows ─ (dash = "click to collapse")

        MINIMIZED:
          - Body is hidden (only title bar visible)
          - Window height is locked to 46px (title bar height)
          - Minimize button shows □ (square = "click to restore")

        This is useful when the user wants the assistant out of
        the way temporarily without closing it entirely.
        """

        # Flip the boolean value.
        # If _is_minimized was True → becomes False
        # If _is_minimized was False → becomes True
        # The "not" keyword inverts a boolean: not True = False, not False = True
        self._is_minimized = not self._is_minimized

        # Show or hide the body based on the new state.
        # setVisible(False) hides the widget completely.
        # setVisible(True) makes it visible again.
        #
        # We pass "not self._is_minimized" because:
        #   When minimized=True  → body should be visible=False (hidden)
        #   When minimized=False → body should be visible=True  (shown)
        self.body.setVisible(not self._is_minimized)

        if self._is_minimized:
            # Collapsed state:
            # setFixedHeight(46) locks BOTH min and max height to 46px,
            # so the window can't be resized while minimized.
            # 46px = exact height of the title bar.
            self.setFixedHeight(46)

            # Change button symbol to □ = "click to expand"
            self.minimize_btn.setText("□")

        else:
            # Expanded state:
            # Remove the height lock by resetting min and max separately.
            # setMinimumHeight(0)        = no minimum (can be any height)
            # setMaximumHeight(16777215) = Qt's internal "no maximum" value
            #                             (2^24 - 1, the largest Qt allows)
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)

            # Resize back to full height
            self.resize(self.width(), 580)

            # Change button symbol back to ─ = "click to collapse"
            self.minimize_btn.setText("─")


    def _on_send(self):
        """
        Handles the user submitting a message.

        Triggered by:
          - Pressing the Enter/Return key in the input field
          - Clicking the → send button

        What it does:
          1. Gets the text from the input field
          2. Returns early (does nothing) if the text is empty
          3. Disables the input and button (prevents double-sending)
          4. Tells chat_panel to show the user's message bubble
          5. Tells chat_panel to show the typing indicator
          6. Clears the input field
          7. Sets a 1.5 second timer to show a fake AI response

        NOTE: Step 7 (the fake response) will be replaced in Step 3
        with a real call to the Ollama AI model running locally.
        """

        # .text() returns whatever is currently in the input field.
        # .strip() removes any spaces or newlines from the start and end.
        # Example: "  hello  " → "hello"
        # Example: "   "      → "" (empty string)
        text = self.input_field.text().strip()

        # If text is empty after stripping, do nothing and return.
        # "return" exits the function immediately — nothing below runs.
        # This prevents sending blank messages.
        if not text:
            return

        # ── Disable input while waiting for AI ────────────────
        #
        # We disable both the text field and the button to prevent
        # the user from sending another message before the first
        # one gets a response. This will be re-enabled in _fake_ai_response().
        self.input_field.setEnabled(False)   # Grey out the text field
        self.send_btn.setEnabled(False)      # Grey out the button

        # ── Show the user's message ───────────────────────────
        #
        # Call the public method on our chat_panel instance.
        # This creates a blue bubble on the right side of the chat.
        self.chat_panel.add_user_message(text)

        # ── Show the typing indicator ─────────────────────────
        #
        # Immediately show "AI is thinking..." animated dots.
        # This gives the user feedback that something is happening.
        self.chat_panel.show_typing()

        # ── Clear the input field ─────────────────────────────
        #
        # Clear the typed text so it's ready for the next message.
        # We do this right away (not after the AI responds) so it
        # feels snappy and responsive.
        self.input_field.clear()

        # ── Schedule the fake AI response ─────────────────────
        #
        # QTimer.singleShot(delay_ms, function) calls function
        # ONCE after delay_ms milliseconds, then stops.
        #
        # 1500ms = 1.5 seconds — long enough to see the typing indicator.
        #
        # Why use "lambda: self._fake_ai_response(text)"?
        # ─────────────────────────────────────────────────────
        # QTimer.singleShot expects a function with NO arguments.
        # But _fake_ai_response needs the 'text' argument.
        #
        # A "lambda" creates a small anonymous function on the fly.
        # lambda: self._fake_ai_response(text)
        # is shorthand for:
        #   def call_with_text():
        #       self._fake_ai_response(text)
        #
        # The lambda "captures" the value of text at the moment
        # this line runs, and passes it to _fake_ai_response later.
        #
        # TODO (Step 3): Replace this with a real Ollama API call.
        QTimer.singleShot(1500, lambda: self._fake_ai_response(text))


    def _fake_ai_response(self, user_text):
        """
        Temporary placeholder that simulates an AI response.

        THIS ENTIRE METHOD will be replaced in Step 3 with a real
        call to the Ollama model running on the user's computer.

        Currently it:
          1. Re-enables the input field and send button
          2. Adds a fake AI response bubble via chat_panel
          3. Shows a diagram placeholder below the response

        The show_diagram=True argument previews the diagram area
        so we can confirm the layout looks correct before Step 4.

        Args:
            user_text (str): What the user typed (echoed back in the reply).
        """

        # Re-enable input so the user can type their next message
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)

        # Return focus to the input field so the user can type
        # immediately without having to click it first.
        self.input_field.setFocus()

        # Show the fake AI response via chat_panel.
        # add_ai_message() also hides the typing indicator automatically
        # (see chat_panel.py's add_ai_message() method).
        #
        # show_diagram=True → also shows the diagram placeholder box
        # below the message (this previews Step 4 functionality).
        self.chat_panel.add_ai_message(
            f"🔄 In Step 3, Ollama will answer: \"{user_text}\"\n\n"
            "For now, here's a preview of how a diagram will appear "
            "below each AI response when we connect Claude in Step 4!",
            show_diagram=True
        )


    # ═══════════════════════════════════════════════════════════
    # SECTION 4: MOUSE DRAG LOGIC
    # ═══════════════════════════════════════════════════════════
    #
    # Since we removed the OS title bar with FramelessWindowHint,
    # we also lost the built-in window dragging. The user can no
    # longer click and drag a title bar to move the window —
    # because there isn't one drawn by the OS anymore.
    #
    # We recreate dragging manually using three mouse event methods.
    # Qt automatically calls these when mouse events happen:
    #
    #   mousePressEvent   — user clicks a mouse button
    #   mouseMoveEvent    — user moves the mouse (with button held)
    #   mouseReleaseEvent — user releases the mouse button
    #
    # Together they implement: "if user clicks title bar and
    # moves mouse while holding, move the window with it."
    #

    def mousePressEvent(self, event):
        """
        Called automatically by Qt when the user presses a mouse button.

        We only start dragging if:
          a) The user pressed the LEFT button (not right or middle click)
          b) The click was INSIDE the title bar area

        We store the offset so the window moves smoothly, keeping the
        clicked point under the mouse (not jumping to a corner).

        Args:
            event (QMouseEvent): Contains info about the click:
                                 which button, where the mouse was, etc.
        """

        # event.button() returns which mouse button was pressed.
        # Qt.LeftButton is the constant for the primary/left button.
        if event.button() == Qt.LeftButton:

            # self.title_bar.geometry() returns a QRect (rectangle)
            # describing the title bar's position and size within this window.
            #
            # .contains(point) returns True if the point is inside
            # that rectangle.
            #
            # event.pos() returns the mouse position relative to this window.
            #
            # So: "did the user click inside the title bar?"
            if self.title_bar.geometry().contains(event.pos()):

                # Mark that we're now in dragging mode
                self._is_dragging = True

                # Calculate and store the OFFSET between:
                #   event.globalPos()            — where the mouse is on the FULL screen
                #   self.frameGeometry().topLeft() — where our window's top-left corner is
                #
                # Example: window top-left is at (100, 200), mouse clicked at (150, 220)
                # Offset = (150-100, 220-200) = (50, 20)
                # This means the user clicked 50px from the left and 20px from the top.
                #
                # We store this offset so that when we move the window,
                # we subtract it — keeping the window in the SAME relative
                # position under the mouse (not snapping the corner to the cursor).
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()


    def mouseMoveEvent(self, event):
        """
        Called automatically by Qt whenever the mouse moves (while over this window).

        If dragging is active, we move the window to follow the mouse,
        subtracting the stored offset so it moves smoothly.

        Args:
            event (QMouseEvent): Contains the current mouse position.
        """

        # Only move if:
        #   self._is_dragging      → drag was started in mousePressEvent
        #   event.buttons() == LeftButton → left button is STILL held down
        #
        # event.buttons() (plural, with 's') returns which buttons are
        # CURRENTLY held. event.button() (singular) only works in press/release.
        if self._is_dragging and event.buttons() == Qt.LeftButton:

            # Move the window's top-left corner to:
            #   (current mouse position on screen) - (stored click offset)
            #
            # Example continuing from above:
            #   Mouse moved to (200, 270) on screen
            #   Offset is (50, 20)
            #   New window position = (200-50, 270-20) = (150, 250)
            #
            # This means the point where the user originally clicked
            # stays under the mouse cursor as they drag — natural and smooth.
            self.move(event.globalPos() - self._drag_pos)


    def mouseReleaseEvent(self, event):
        """
        Called automatically by Qt when the user releases a mouse button.

        We simply end the drag by setting _is_dragging back to False.
        The next mouseMoveEvent will then do nothing (since the condition
        self._is_dragging is False).

        Args:
            event (QMouseEvent): Contains info about the button release.
                                 (Not used here, but required by Qt's signature.)
        """
        # End the drag operation
        self._is_dragging = False


    # ═══════════════════════════════════════════════════════════
    # SECTION 5: STYLING
    # ═══════════════════════════════════════════════════════════

    def _apply_styles(self):
        """
        Applies CSS styling to all the WINDOW SHELL components.

        Note: Chat bubble styles are in chat_panel.py's _apply_styles().
        This method only styles: container, title bar, input, buttons.

        Qt Style Sheets (QSS) work like web CSS:
          - Selectors target widgets: QWidget#container, QPushButton#sendBtn
          - Properties set visual attributes: background-color, border-radius
          - Pseudo-states add conditional styles: :hover, :focus, :disabled

        Colour palette:
          #1A1B2E — deep navy (main card background)
          #252640 — slightly lighter navy (title bar left gradient stop)
          #4A5AE8 — indigo blue (buttons, focus rings, accents)
          #E8E9FF — near-white (primary text colour)
          rgba(255,255,255,N) — white at N% opacity (subtle overlays)
        """

        self.setStyleSheet("""

            /* ── Outer FloatingWindow widget ────────────────────
               Must be transparent so the rounded container card
               doesn't have white square corners behind it.
               The actual background colour is on #container below.
            ─────────────────────────────────────────────────── */
            FloatingWindow {
                background: transparent;
            }

            /* ── Main card container ────────────────────────────
               This is the dark rectangle the user sees.
               border-radius: 16px rounds all four corners.
               border: 1px solid — a very subtle light edge glow.
            ─────────────────────────────────────────────────── */
            QWidget#container {
                background-color: #1A1B2E;
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.08);
            }

            /* ── Title bar ───────────────────────────────────────
               qlineargradient draws a left-to-right colour gradient:
                 x1:0, y1:0 = start at left
                 x2:1, y2:0 = end at right
                 stop:0 #252640 = left colour (slightly lighter navy)
                 stop:1 #1A1B2E = right colour (same as main background)
               This creates a subtle depth effect.

               border-radius: 16px 16px 0 0 rounds only the TOP corners.
               Values are: top-left top-right bottom-right bottom-left
               (clockwise from top-left, same as CSS shorthand)
            ─────────────────────────────────────────────────── */
            QWidget#titleBar {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #252640,
                    stop:1 #1A1B2E
                );
                border-radius: 16px 16px 0 0;
                border-bottom: 1px solid rgba(255,255,255,0.06);
            }

            /* Title text — "Study Assistant" */
            QLabel#titleLabel {
                color: #E8E9FF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: 600;         /* 600 = semi-bold (between normal and bold) */
                letter-spacing: 0.5px;   /* Tiny space between letters for readability */
            }

            /* ── Body area ───────────────────────────────────────
               Transparent — lets the container's dark background
               show through without adding a second layer of colour.
            ─────────────────────────────────────────────────── */
            QWidget#body {
                background: transparent;
            }

            /* ── Input row ───────────────────────────────────────
               Also transparent — same reason as body.
            ─────────────────────────────────────────────────── */
            QWidget#inputRow {
                background: transparent;
            }

            /* ── Text input field ────────────────────────────────
               Dark semi-transparent background so it blends into
               the card without being invisible.
               padding: 0 12px = 0px top/bottom, 12px left/right
               (inner spacing so text doesn't touch the border).
            ─────────────────────────────────────────────────── */
            QLineEdit#inputField {
                background-color: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                color: #E8E9FF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                padding: 0 12px;
            }

            /* Input field focused state — when the user has clicked it.
               Blue border ring signals "this is active/ready to type."
               Matches common web input focus patterns (e.g. Google Search). */
            QLineEdit#inputField:focus {
                border: 1px solid #4A5AE8;
                background-color: rgba(74,90,232,0.1); /* Very subtle blue tint */
            }

            /* The "Ask anything..." hint text (only visible when empty) */
            QLineEdit#inputField::placeholder {
                color: rgba(255,255,255,0.25); /* Dim — clearly not real content */
            }

            /* Disabled state — when the AI is "thinking" and we've
               locked the input to prevent double-sending */
            QLineEdit#inputField:disabled {
                color: rgba(255,255,255,0.3);
                background-color: rgba(255,255,255,0.03);
            }

            /* ── Send button ─────────────────────────────────────
               Solid indigo blue square with rounded corners.
               Three states: default, hovered, pressed, disabled.
            ─────────────────────────────────────────────────── */
            QPushButton#sendBtn {
                background-color: #4A5AE8;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }

            /* Slightly lighter blue on mouse hover — visual feedback */
            QPushButton#sendBtn:hover {
                background-color: #5A6AF8;
            }

            /* Slightly darker when actually being clicked — "pressed" feel */
            QPushButton#sendBtn:pressed {
                background-color: #3A4AD8;
            }

            /* Faded out when disabled (while AI is responding) */
            QPushButton#sendBtn:disabled {
                background-color: rgba(74,90,232,0.3);
            }

            /* ── Resize grip ─────────────────────────────────────
               Transparent background — the system's resize cursor
               appears on hover automatically without a visible box.
            ─────────────────────────────────────────────────── */
            QSizeGrip#sizeGrip {
                background: transparent;
                width: 14px;
                height: 14px;
            }

        """)
