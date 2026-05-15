# ============================================================
# main.py — Entry point for the Visual Study Assistant
# ============================================================
#
# WHAT IS THIS FILE?
# ------------------
# This is the FIRST file Python runs when you start the app.
# Think of it like the "front door" of the program.
# Its only job is to:
#   1. Set up the PyQt5 application environment
#   2. Create the floating window
#   3. Show it on screen
#   4. Keep the app running until the user closes it
#
# HOW TO RUN THE APP:
# -------------------
#   python main.py
#
# ============================================================
 
 
# 'sys' is a built-in Python module that lets us interact with
# the operating system — we use it to properly exit the app.
import sys
 
# QApplication is the foundation of every PyQt5 app.
# It manages the app's lifecycle, settings, and event loop.
# You MUST create one before creating any windows or widgets.
from PyQt5.QtWidgets import QApplication
 
# This imports our custom floating window class from the ui folder.
# The file ui/floating_window.py contains all the window logic.
from ui.floating_window import FloatingWindow
 
 
def main():
    """
    The main function — this runs everything.
 
    In Python, wrapping your startup code in a function called
    main() is a common good practice. It keeps things organised
    and makes it easier to understand what happens at startup.
    """
 
    # ── Step 1: Create the QApplication ──────────────────────
    #
    # QApplication is the heart of any PyQt5 program.
    # It handles things like:
    #   - The event loop (listening for clicks, key presses, etc.)
    #   - System settings (fonts, colors, screen info)
    #   - App-level behaviour (what happens when last window closes)
    #
    # sys.argv passes any command-line arguments to Qt.
    # Even if you don't use command-line args, Qt expects this.
    app = QApplication(sys.argv)
 
    # This tells the app: "When the last window is closed, quit."
    # Without this, the app might keep running invisibly in the
    # background even after the window is gone.
    app.setQuitOnLastWindowClosed(True)
 
    # ── Step 2: Create the floating window ───────────────────
    #
    # This creates an instance of our FloatingWindow class.
    # At this point, the window exists in memory but isn't
    # visible yet — it's like building a house but not opening
    # the front door.
    window = FloatingWindow()
 
    # ── Step 3: Show the window ───────────────────────────────
    #
    # .show() makes the window visible on screen.
    # This triggers the window to paint itself and appear
    # floating on top of the user's other windows.
    window.show()
 
    # ── Step 4: Start the event loop ─────────────────────────
    #
    # app.exec_() starts the "event loop" — this is a loop that
    # runs forever, constantly listening for things like:
    #   - Mouse clicks
    #   - Key presses
    #   - Window resize
    #   - Messages from the AI
    #
    # The app stays open and responsive because of this loop.
    # It only stops when the user closes the window.
    #
    # sys.exit() passes the exit code back to the operating
    # system so it knows the app ended cleanly (code 0 = success).
    sys.exit(app.exec_())
 
 
# ── What is this if-block? ────────────────────────────────────
#
# This is a Python convention that means:
# "Only run main() if this file is being run directly."
#
# If someone imports this file from another file (like a test),
# main() will NOT run automatically — which is usually what
# you want. It only runs when you do: python main.py
#
# __name__ is a special Python variable:
#   - It equals "__main__" when you run the file directly
#   - It equals the module name when imported elsewhere
#
if __name__ == "__main__":
    main()