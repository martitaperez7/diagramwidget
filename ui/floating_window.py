# ============================================================
# ui/floating_window.py — The main floating widget window
# ============================================================
#
# WHAT IS THIS FILE?
# ------------------
# This file defines the FloatingWindow class — the actual
# visual panel that floats on top of the user's screen.
#
# It handles everything about the window's appearance and
# behaviour, including:
#   - Staying on top of all other windows
#   - The custom title bar (since we removed the OS one)
#   - Dragging the window by clicking the title bar
#   - Resizing by dragging the bottom-right corner
#   - The chat message area
#   - The text input bar at the bottom
#   - Minimising to just the title bar
#   - All the visual styling (dark glassy theme)
#
# WHAT IS A CLASS?
# ----------------
# A class is like a blueprint. FloatingWindow is our blueprint
# for "what a floating study assistant window looks like and
# how it behaves." When we write FloatingWindow() in main.py,
# we're building one actual window from that blueprint.
#
# ============================================================


# ── Imports ───────────────────────────────────────────────────
#
# PyQt5 is the library that lets us build desktop windows and UIs.
# We import specific "widgets" (UI components) that we need.
#
# QWidget      — the base class for all UI elements; a blank canvas
# QVBoxLayout  — arranges widgets in a vertical stack (top to bottom)
# QHBoxLayout  — arranges widgets in a horizontal row (left to right)
# QLabel       — displays text or images
# QPushButton  — a clickable button
# QSizeGrip    — the small triangle in the corner for resizing
# QTextEdit    — a multi-line text editor (not used yet, for later)
# QLineEdit    — a single-line text input field
# QScrollArea  — a scrollable container for content that overflows
# QFrame       — a container widget with optional borders
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizeGrip, QTextEdit, QLineEdit,
    QScrollArea, QFrame
)

# Qt       — contains constants like Qt.LeftButton, Qt.AlignTop, etc.
# QPoint   — represents a 2D point (x, y) — used to track mouse position
# QSize    — represents a width and height
from PyQt5.QtCore import Qt, QPoint, QSize

# QFont    — lets us set font family and size on widgets
# QColor   — represents a colour (not directly used here but useful later)
# QPalette — controls colour schemes for widgets
# QIcon    — loads image icons (not used yet, reserved for later steps)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon


# ── The FloatingWindow Class ──────────────────────────────────
#
# This class inherits from QWidget, which means it IS a window/widget.
# By inheriting QWidget, we get all its built-in window behaviour for
# free, and then we customise it to do what we want.
#
# Think of it like: QWidget is a plain white room, and FloatingWindow
# is our decorated, furnished version of that room.
#
class FloatingWindow(QWidget):

    def __init__(self):
        """
        __init__ is the constructor — it runs automatically when you
        create a FloatingWindow() object. This is where we set up
        everything the window needs to exist and look correct.

        'self' refers to THIS specific window instance. Every method
        in a class receives 'self' as the first argument so it can
        access and modify the object's own properties.
        """

        # ALWAYS call the parent class constructor first.
        # Since FloatingWindow inherits from QWidget, we need to
        # let QWidget set itself up before we customise it.
        # super() refers to the parent class (QWidget).
        super().__init__()

        # ── Window Flags ──────────────────────────────────────
        #
        # Window flags are special settings that control how the
        # operating system treats this window. We combine multiple
        # flags using the | (bitwise OR) operator.
        #
        # Qt.WindowStaysOnTopHint
        #   → Tells the OS: "always keep this window in front."
        #     Even when the user clicks on Chrome or another app,
        #     our widget stays visible on top.
        #
        # Qt.FramelessWindowHint
        #   → Removes the default OS window border and title bar
        #     (the bar with the app name, minimize, maximize, close).
        #     We remove it so we can draw our OWN custom title bar
        #     that matches our design perfectly.
        #
        # Qt.Tool
        #   → Marks this as a "tool window." This means it won't
        #     appear as a separate entry in the taskbar/dock, which
        #     keeps the taskbar clean. It behaves more like a widget
        #     that belongs to the user's workspace.
        #
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint  |
            Qt.Tool
        )

        # WA_TranslucentBackground allows the window background to
        # be transparent. This is what allows us to have rounded
        # corners — the corners are actually transparent, not white.
        # Without this, rounded corners would show as white squares.
        self.setAttribute(Qt.WA_TranslucentBackground)

        # ── Initial Size & Position ───────────────────────────
        #
        # Set the window's starting size: 380 pixels wide, 580 tall.
        # The user can resize it after launch using the grip handle.
        self.resize(380, 580)

        # Place the window in the bottom-right corner of the screen.
        # We defined this as a separate method below to keep things tidy.
        self._place_bottom_right()

        # ── Instance Variables ────────────────────────────────
        #
        # These are variables that belong to THIS window object.
        # We prefix them with self. so they're accessible in all
        # methods of this class (not just the one where they're created).
        #
        # _drag_pos: Stores the mouse position when dragging starts.
        #            QPoint(0,0) means "no position yet."
        self._drag_pos = QPoint()

        # _is_dragging: A True/False flag tracking whether the user
        #               is currently holding down the mouse and dragging.
        self._is_dragging = False

        # _is_minimized: Tracks whether the panel is collapsed (True)
        #                or fully open (False).
        self._is_minimized = False

        # ── Build and Style the UI ────────────────────────────
        #
        # We call these two methods to actually construct the
        # visual components and apply colours/fonts to them.
        # Separating them makes the code easier to navigate.
        self._build_ui()
        self._apply_styles()


    # ═══════════════════════════════════════════════════════════
    # SECTION 1: PLACEMENT
    # ═══════════════════════════════════════════════════════════

    def _place_bottom_right(self):
        """
        Calculates the bottom-right corner of the user's screen and
        moves the window there, with a small 20px margin from the edges.

        Why bottom-right? That's where most apps put floating helpers
        (like chat widgets on websites), so users intuitively look there.
        """

        # QDesktopWidget gives us information about the user's screen(s).
        # We import it here (inside the method) rather than at the top
        # to keep imports logically grouped — this is the only place it's used.
        from PyQt5.QtWidgets import QDesktopWidget

        # availableGeometry() returns the usable screen area (excluding
        # the taskbar). This ensures our window doesn't hide behind it.
        screen = QDesktopWidget().availableGeometry()

        # Calculate x (horizontal) position:
        # Start from the right edge of the screen, subtract our window
        # width, then subtract 20 more pixels for a nice margin.
        x = screen.width() - self.width() - 20

        # Calculate y (vertical) position:
        # Same logic — start from the bottom, go up by our height + margin.
        y = screen.height() - self.height() - 20

        # Move the window to those coordinates.
        # (0, 0) is the top-left corner of the screen.
        self.move(x, y)


    # ═══════════════════════════════════════════════════════════
    # SECTION 2: UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════

    def _build_ui(self):
        """
        Constructs all the visual components of the floating panel.

        Think of this like assembling furniture — we create each piece
        (title bar, chat area, input bar) and then stack them together
        inside a container.

        LAYOUT SYSTEM explained:
        +─────────────────────────+
        |  outer_layout (QVBox)   |  <- Holds the container
        |  +───────────────────+  |
        |  |  container        |  |  <- The dark rounded card
        |  |  +─────────────+  |  |
        |  |  |  title_bar  |  |  |  <- Drag handle + buttons
        |  |  +─────────────+  |  |
        |  |  |  body        |  |  |  <- Chat + input (hideable)
        |  |  |  +────────+  |  |  |
        |  |  |  | chat   |  |  |  |  <- Scrollable messages
        |  |  |  +────────+  |  |  |
        |  |  |  | input  |  |  |  |  <- Text field + send button
        |  |  |  +────────+  |  |  |
        |  |  +─────────────+  |  |
        |  |  |  [grip]      |  |  |  <- Resize handle (bottom-right)
        |  |  +─────────────+  |  |
        |  +───────────────────+  |
        +─────────────────────────+
        """

        # ── Outer Layout ──────────────────────────────────────
        #
        # Every widget needs a layout to organise its children.
        # QVBoxLayout stacks things vertically (top to bottom).
        # We pass 'self' to attach this layout to the FloatingWindow itself.
        outer_layout = QVBoxLayout(self)

        # setContentsMargins(left, top, right, bottom) sets the padding
        # around the inside edges of the layout. We use 0 everywhere
        # because our container widget handles its own rounded styling.
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # setSpacing sets the gap between items in the layout.
        # 0 means no gap — everything is flush together.
        outer_layout.setSpacing(0)

        # ── Container Widget (the dark rounded card) ──────────
        #
        # This QWidget acts as the visible "card" that holds everything.
        # The actual dark background and rounded corners are applied
        # to this widget via CSS in _apply_styles().
        #
        # setObjectName gives it a CSS class name — like giving an
        # HTML element an id="container" so we can target it in CSS.
        self.container = QWidget()
        self.container.setObjectName("container")

        # Create a vertical layout inside the container.
        # Note: we pass self.container to attach the layout to it.
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ── Title Bar ─────────────────────────────────────────
        #
        # We build the title bar in a separate method to keep
        # _build_ui() readable. It returns a QWidget that we add here.
        self.title_bar = self._build_title_bar()

        # addWidget() places the title bar at the top of the container.
        container_layout.addWidget(self.title_bar)

        # ── Body (chat area + input field) ────────────────────
        #
        # The "body" is everything below the title bar.
        # We put it in its own widget so we can hide/show the entire
        # body at once when the user clicks the minimize button.
        self.body = QWidget()
        self.body.setObjectName("body")
        body_layout = QVBoxLayout(self.body)

        # 12px padding on left/right, 8px on top/bottom — gives
        # the content some breathing room from the card edges.
        body_layout.setContentsMargins(12, 8, 12, 8)
        body_layout.setSpacing(8)

        # Build and add the scrollable chat message area.
        # This takes up most of the body space.
        self.chat_area = self._build_chat_area()
        body_layout.addWidget(self.chat_area)

        # Build and add the input bar at the very bottom.
        self.input_row = self._build_input_row()
        body_layout.addWidget(self.input_row)

        container_layout.addWidget(self.body)

        # ── Resize Grip ───────────────────────────────────────
        #
        # QSizeGrip is a built-in PyQt5 widget that creates a
        # small draggable triangle in the corner for resizing the window.
        # We use an HBoxLayout with addStretch() to push it to the right.
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 4, 4)  # Small margin from edges
        grip_row.addStretch()  # Push everything to the right

        self.size_grip = QSizeGrip(self)
        self.size_grip.setObjectName("sizeGrip")
        grip_row.addWidget(self.size_grip)

        # addLayout() adds a layout (not a widget) to another layout.
        container_layout.addLayout(grip_row)

        # Finally, add the fully-built container to the outermost layout.
        outer_layout.addWidget(self.container)


    def _build_title_bar(self):
        """
        Builds and returns the custom title bar widget.

        Since we removed the OS title bar (FramelessWindowHint),
        we need to draw our own. This one has:
          - A brain emoji icon
          - The app name "Study Assistant"
          - A minimize button (-)
          - A close button (x)

        The title bar also doubles as our drag handle — the mouse
        drag events check if the click was inside this widget.

        Returns:
            QWidget: The completed title bar widget.
        """

        # Create a plain QWidget to act as the title bar container.
        bar = QWidget()
        bar.setObjectName("titleBar")  # CSS target name

        # Fix the height at 46px — title bars should be consistent.
        bar.setFixedHeight(46)

        # Horizontal layout: icon -> title -> [stretch] -> minimize -> close
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 10, 0)  # Left padding of 14px
        layout.setSpacing(8)  # 8px between each item

        # ── App Icon (brain emoji) ─────────────────────────────
        icon_label = QLabel("🧠")
        # Use the emoji font at size 16 so it renders properly
        icon_label.setFont(QFont("Segoe UI Emoji", 16))

        # ── App Title ─────────────────────────────────────────
        title_label = QLabel("Study Assistant")
        title_label.setObjectName("titleLabel")  # Styled in CSS

        # Add icon and title to the layout
        layout.addWidget(icon_label)
        layout.addWidget(title_label)

        # addStretch() adds invisible flexible space.
        # This pushes everything after it to the RIGHT side of the bar.
        # Without this, the buttons would sit right next to the title.
        layout.addStretch()

        # ── Control Buttons ───────────────────────────────────
        #
        # We use a helper method _make_control_btn() to avoid
        # repeating the same button-creation code twice.
        # Arguments: symbol, colour, what to do when clicked.

        # Minimize button — yellow, collapses the body panel
        self.minimize_btn = self._make_control_btn(
            symbol="─",
            color="#F0C040",
            callback=self._toggle_minimize
        )

        # Close button — red, closes and exits the app
        self.close_btn = self._make_control_btn(
            symbol="✕",
            color="#FF6058",
            callback=self.close  # .close() is a built-in QWidget method
        )

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.close_btn)

        return bar


    def _make_control_btn(self, symbol, color, callback):
        """
        A helper method that creates a small circular window control button.

        Rather than writing the same button setup code twice (once for
        minimize, once for close), we put it in one reusable method.

        Args:
            symbol   (str):      The text/icon to show inside the button.
            color    (str):      Hex color code for the button background.
            callback (function): The function to call when the button is clicked.

        Returns:
            QPushButton: A small styled circular button.
        """

        btn = QPushButton(symbol)

        # Make the button a perfect 22x22 pixel square.
        # Combined with border-radius: 11px in CSS, this makes it a circle.
        btn.setFixedSize(22, 22)
        btn.setObjectName("controlBtn")

        # Apply inline CSS styling specific to this button.
        # We use an f-string so the {color} variable is inserted into the CSS.
        # Note: In PyQt5 CSS, {{ and }} are escaped curly braces
        # (they represent literal { } in the output string).
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 11px;       /* Makes the square into a circle */
                color: rgba(0,0,0,0.6);    /* Slightly transparent black symbol */
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: rgba(0,0,0,0.9);    /* Darker symbol on hover for feedback */
            }}
        """)

        # .connect() links the button's "clicked" signal to a function.
        # A "signal" is an event that Qt fires when something happens.
        # When the button is clicked, Qt emits the "clicked" signal,
        # which then calls our callback function automatically.
        btn.clicked.connect(callback)

        return btn


    def _build_chat_area(self):
        """
        Creates and returns the scrollable chat message display area.

        This uses QScrollArea to allow messages to scroll vertically
        when the conversation gets long. The messages themselves are
        added dynamically in _on_send() as the user chats.

        Returns:
            QScrollArea: The scrollable container for chat messages.
        """

        # QScrollArea is a container that adds scrollbars automatically
        # when its content is taller than its visible area.
        scroll = QScrollArea()
        scroll.setObjectName("chatScroll")

        # setWidgetResizable(True) means the inner widget will stretch
        # to fill the scroll area's width automatically.
        scroll.setWidgetResizable(True)

        # Hide the horizontal scrollbar — chat messages should only
        # scroll up/down, never left/right.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # ── Inner content widget ──────────────────────────────
        #
        # QScrollArea needs a single child widget to scroll.
        # We create a plain QWidget and give it a vertical layout.
        # Message bubbles will be added to this layout one by one.
        self.chat_content = QWidget()
        self.chat_content.setObjectName("chatContent")

        # We save this layout as self.chat_layout so that _on_send()
        # can access it later to add new message bubbles.
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(4, 8, 4, 8)
        self.chat_layout.setSpacing(10)  # 10px gap between messages

        # AlignTop means messages stack from the top down.
        # Without this, a single message would be centred vertically.
        self.chat_layout.setAlignment(Qt.AlignTop)

        # ── Welcome Message ───────────────────────────────────
        #
        # Show a friendly greeting when the app first opens.
        # This is an AI bubble (is_user=False = left-aligned, grey).
        welcome = self._make_message_bubble(
            "👋 Hi! I'm your Visual Study Assistant.\n\n"
            "Ask me anything — I'll explain it with diagrams "
            "and visuals to help it stick.\n\n"
            "Try: \"How does the water cycle work?\"",
            is_user=False
        )
        self.chat_layout.addWidget(welcome)

        # Assign the inner widget to the scroll area.
        # This is the required final step to make QScrollArea work.
        scroll.setWidget(self.chat_content)

        return scroll


    def _make_message_bubble(self, text, is_user=False):
        """
        Creates and returns a single styled chat message bubble.

        This method is called every time a new message needs to be shown
        (both for user messages and AI responses). The style differs
        depending on who sent the message:

          - AI messages   -> left-aligned, grey/transparent background
          - User messages -> right-aligned, blue background

        Args:
            text    (str):  The message text to display.
            is_user (bool): True if this is the user's message, False for AI.

        Returns:
            QLabel: A styled label widget showing the message.
        """

        # QLabel displays text. It's the simplest text widget in Qt.
        bubble = QLabel(text)

        # wordWrap allows text to wrap to the next line when it's
        # too wide to fit on one line. Essential for chat bubbles.
        bubble.setWordWrap(True)

        # Assign a CSS object name based on who sent the message.
        # "userBubble" -> blue, pushed right
        # "aiBubble"   -> grey, on the left
        bubble.setObjectName("userBubble" if is_user else "aiBubble")

        bubble.setAlignment(Qt.AlignLeft)

        # TextSelectableByMouse lets users highlight and copy the text.
        # This is important so users can copy AI explanations.
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)

        return bubble


    def _build_input_row(self):
        """
        Creates and returns the text input bar at the bottom of the panel.

        This contains:
          - A QLineEdit: a single-line text field where the user types
          - A send button (->): submits the message

        Both the Enter key and the send button trigger _on_send().

        Returns:
            QWidget: The input row container widget.
        """

        # Container widget for the input row
        row = QWidget()
        row.setObjectName("inputRow")

        # Horizontal layout: [text field ──────────────] [->]
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 4, 0, 0)  # Small top padding
        layout.setSpacing(8)

        # ── Text Input Field ──────────────────────────────────
        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")

        # Placeholder text is the greyed-out hint shown when empty.
        self.input_field.setPlaceholderText("Ask anything to learn visually...")
        self.input_field.setFixedHeight(38)

        # returnPressed is a signal that fires when the user presses Enter.
        # We connect it to our _on_send() method so Enter submits the message.
        self.input_field.returnPressed.connect(self._on_send)

        # ── Send Button ───────────────────────────────────────
        send_btn = QPushButton("→")
        send_btn.setObjectName("sendBtn")
        send_btn.setFixedSize(38, 38)  # Square button, same height as input
        send_btn.clicked.connect(self._on_send)

        layout.addWidget(self.input_field)
        layout.addWidget(send_btn)

        return row


    # ═══════════════════════════════════════════════════════════
    # SECTION 3: ACTIONS (what happens when things are clicked)
    # ═══════════════════════════════════════════════════════════

    def _toggle_minimize(self):
        """
        Toggles the window between its full size and a collapsed
        "title bar only" state.

        When minimized:
          - The body (chat + input) is hidden
          - The window is locked to 46px tall (just the title bar)
          - The minimize button symbol changes from - to []

        When restored:
          - The body becomes visible again
          - Height constraints are removed so it can resize freely
          - The window snaps back to 580px tall
          - The button symbol reverts to -
        """

        # Flip the boolean: True becomes False, False becomes True.
        self._is_minimized = not self._is_minimized

        # setVisible(False) hides the body completely (chat + input disappear).
        # setVisible(True) makes it visible again.
        # We negate _is_minimized: when minimized=True, body is NOT visible.
        self.body.setVisible(not self._is_minimized)

        if self._is_minimized:
            # Lock the window to exactly 46px (title bar height only).
            # setFixedHeight sets BOTH the minimum and maximum height,
            # so the user can't resize it while minimized.
            self.setFixedHeight(46)
            self.minimize_btn.setText("□")  # Square icon = "click to restore"
        else:
            # Remove the fixed height so the window can be freely resized again.
            # 0 = no minimum height restriction
            # 16777215 = Qt's built-in maximum value (essentially "no limit")
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)

            # Resize back to the normal full height
            self.resize(self.width(), 580)
            self.minimize_btn.setText("─")  # Dash icon = "click to minimize"


    def _on_send(self):
        """
        Handles what happens when the user sends a message.

        Called when:
          - The user presses Enter in the input field
          - The user clicks the -> send button

        Currently (Step 1) this is a PLACEHOLDER:
          - It shows the user's message as a blue bubble
          - It shows a fake "AI response coming soon" grey bubble
          - It clears the input field
          - It scrolls to the latest message

        In Step 3, we will replace the placeholder AI response
        with a real call to the Ollama AI model.
        """

        # Get the text the user typed, and remove any leading/trailing spaces.
        # .strip() removes whitespace like spaces and newlines from both ends.
        text = self.input_field.text().strip()

        # If the user pressed Enter with an empty field, do nothing.
        if not text:
            return

        # ── Show the user's message ───────────────────────────
        #
        # Create a blue bubble with the user's text and add it
        # to the bottom of the chat layout.
        user_bubble = self._make_message_bubble(text, is_user=True)
        self.chat_layout.addWidget(user_bubble)

        # ── Show a placeholder AI reply ───────────────────────
        #
        # TODO (Step 3): Replace this with a real call to Ollama.
        # For now we just show a notice so the UI feels interactive.
        ai_bubble = self._make_message_bubble(
            "🔄 AI response coming in Step 3! (Ollama integration)",
            is_user=False
        )
        self.chat_layout.addWidget(ai_bubble)

        # Clear the input field so it's ready for the next message.
        self.input_field.clear()

        # ── Auto-scroll to bottom ─────────────────────────────
        #
        # After adding new messages, scroll down so the latest
        # message is always visible without the user having to scroll.
        #
        # verticalScrollBar().maximum() is the furthest scroll position.
        # Setting the value to maximum() scrolls all the way to the bottom.
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )


    # ═══════════════════════════════════════════════════════════
    # SECTION 4: MOUSE DRAG LOGIC
    # ═══════════════════════════════════════════════════════════
    #
    # Since we removed the OS title bar, we lost the built-in
    # window-dragging behaviour. We have to recreate it manually
    # by tracking mouse events.
    #
    # The three methods below work together:
    #   1. mousePressEvent   -> "mouse button down" — start drag
    #   2. mouseMoveEvent    -> "mouse moving"       — move window
    #   3. mouseReleaseEvent -> "mouse button up"    — stop drag
    #

    def mousePressEvent(self, event):
        """
        Called automatically by Qt when the user presses a mouse button.

        We check if:
          a) It's the LEFT mouse button (not right-click)
          b) The click happened inside the title bar area

        If both are true, we start tracking the drag.

        Args:
            event: Qt's mouse event object, containing info about the click.
        """

        if event.button() == Qt.LeftButton:

            # self.title_bar.geometry() returns a rectangle describing
            # where the title bar sits within the window.
            # .contains(event.pos()) checks if the click position is inside it.
            if self.title_bar.geometry().contains(event.pos()):
                self._is_dragging = True

                # Record the offset between the mouse position and
                # the window's top-left corner.
                #
                # event.globalPos() -> mouse position on the ENTIRE screen
                # self.frameGeometry().topLeft() -> window's top-left on screen
                #
                # We store the DIFFERENCE so that when we move the window,
                # it follows the mouse smoothly without jumping to the cursor.
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()


    def mouseMoveEvent(self, event):
        """
        Called automatically by Qt whenever the mouse moves.

        If we're in drag mode (the user is holding the left button on
        the title bar), we move the window to follow the mouse.

        Args:
            event: Qt's mouse event object, with the current mouse position.
        """

        # Only move if we're actively dragging with the left button held.
        if self._is_dragging and event.buttons() == Qt.LeftButton:

            # Move the window so its top-left corner is at:
            #   (current mouse position) minus (the saved offset)
            #
            # This keeps the window pinned to where the user grabbed it,
            # rather than snapping the window's corner to the cursor.
            self.move(event.globalPos() - self._drag_pos)


    def mouseReleaseEvent(self, event):
        """
        Called automatically by Qt when the user releases a mouse button.

        We simply stop the drag by setting _is_dragging back to False.

        Args:
            event: Qt's mouse event object (not used here, but required by Qt).
        """
        self._is_dragging = False


    # ═══════════════════════════════════════════════════════════
    # SECTION 5: VISUAL STYLING
    # ═══════════════════════════════════════════════════════════

    def _apply_styles(self):
        """
        Applies CSS-like styling to the entire widget.

        PyQt5 uses "Qt Style Sheets" (QSS) which are very similar to
        CSS used in web development. We target widgets by:
          - Class name:  QWidget, QPushButton, QLineEdit, etc.
          - Object name: QWidget#container, QLabel#titleLabel, etc.
                         (set via setObjectName() earlier in the code)
          - State:       QPushButton:hover, QLineEdit:focus, etc.

        COLOUR GUIDE for this theme:
          #1A1B2E — Deep dark navy   (main background)
          #252640 — Slightly lighter (title bar gradient start)
          #4A5AE8 — Bright indigo    (user bubbles, send button, focus ring)
          #E8E9FF — Near white       (primary text)
          #D0D1F0 — Soft lavender    (AI message text)
          rgba(255,255,255,0.06) — Very subtle white overlay (AI bubbles)
        """

        self.setStyleSheet("""

            /* ═══════════════════════════════════════════
               OUTER WINDOW
               The FloatingWindow itself is transparent.
               This is what allows our rounded container
               to have actual transparent corners instead
               of ugly white squares.
            ═══════════════════════════════════════════ */
            FloatingWindow {
                background: transparent;
            }


            /* ═══════════════════════════════════════════
               MAIN CONTAINER CARD
               This is the visible dark panel.
               border-radius: 16px rounds all four corners.
               The semi-transparent border adds a subtle glow edge.
            ═══════════════════════════════════════════ */
            QWidget#container {
                background-color: #1A1B2E;
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }


            /* ═══════════════════════════════════════════
               TITLE BAR
               Uses a linear gradient from left to right:
                 left  (#252640) -> slightly lighter navy
                 right (#1A1B2E) -> same as container bg
               This creates a subtle depth effect.
               Only the TOP two corners are rounded to match
               the container card shape.
            ═══════════════════════════════════════════ */
            QWidget#titleBar {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #252640,
                    stop:1 #1A1B2E
                );
                border-radius: 16px 16px 0 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }

            /* Title text styling */
            QLabel#titleLabel {
                color: #E8E9FF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }


            /* ═══════════════════════════════════════════
               BODY AREA
               Transparent so the container background
               shows through without double-colouring.
            ═══════════════════════════════════════════ */
            QWidget#body {
                background: transparent;
            }


            /* ═══════════════════════════════════════════
               CHAT SCROLL AREA
               Also transparent — we don't want it to
               draw its own background colour.
               border: none removes the default box border.
            ═══════════════════════════════════════════ */
            QScrollArea#chatScroll {
                background: transparent;
                border: none;
            }

            /* Qt adds wrapper widgets inside QScrollArea.
               This targets them to also be transparent. */
            QScrollArea#chatScroll > QWidget > QWidget {
                background: transparent;
            }

            /* Vertical scrollbar — thin and subtle */
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.04);
                width: 4px;
                border-radius: 2px;
            }

            /* The draggable part of the scrollbar */
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 2px;
                min-height: 20px;
            }

            QWidget#chatContent {
                background: transparent;
            }


            /* ═══════════════════════════════════════════
               MESSAGE BUBBLES

               aiBubble   — AI messages, grey, left side
               userBubble — User messages, blue, right side

               border-radius: 12px rounds all corners.
               We flatten ONE corner on each bubble to
               make it look like a traditional chat bubble:
                 AI:   top-left  = 4px  -> points left
                 User: bottom-right = 4px -> points right
            ═══════════════════════════════════════════ */
            QLabel#aiBubble {
                background-color: rgba(255, 255, 255, 0.06);
                color: #D0D1F0;
                border-radius: 12px;
                border-top-left-radius: 4px;
                padding: 10px 14px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }

            QLabel#userBubble {
                background-color: #4A5AE8;
                color: #FFFFFF;
                border-radius: 12px;
                border-bottom-right-radius: 4px;
                padding: 10px 14px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                margin-left: 30px;
            }


            /* ═══════════════════════════════════════════
               INPUT ROW
            ═══════════════════════════════════════════ */
            QWidget#inputRow {
                background: transparent;
            }

            QLineEdit#inputField {
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: #E8E9FF;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                padding: 0 12px;
            }

            /* Blue border ring when the field is focused */
            QLineEdit#inputField:focus {
                border: 1px solid #4A5AE8;
                background-color: rgba(74, 90, 232, 0.1);
            }

            /* The greyed-out hint text */
            QLineEdit#inputField::placeholder {
                color: rgba(255, 255, 255, 0.25);
            }

            /* Send button — default state */
            QPushButton#sendBtn {
                background-color: #4A5AE8;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }

            /* Send button on hover */
            QPushButton#sendBtn:hover {
                background-color: #5A6AF8;
            }

            /* Send button when clicked */
            QPushButton#sendBtn:pressed {
                background-color: #3A4AD8;
            }


            /* ═══════════════════════════════════════════
               RESIZE GRIP
               Transparent so only the resize cursor
               appears on hover, no background box.
            ═══════════════════════════════════════════ */
            QSizeGrip#sizeGrip {
                background: transparent;
                width: 14px;
                height: 14px;
            }

        """)