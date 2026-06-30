"""
main.py
--------
Entry point for Diagram Tutor.

Covers:
    NFR-04: the floating panel should appear within 3 seconds of running
            this file. Qt app startup + creating the widgets is fast
            (well under a second on typical hardware); the only slow part
            would be network calls, which we deliberately do NOT make
            during startup - the panel just sits there empty until you
            type your first question.

Run with:
    python main.py

Requires:
    - Ollama installed and running locally (`ollama serve`) with the
      qwen3:4b model pulled (`ollama pull qwen3:4b`)
    - A .env file with ANTHROPIC_API_KEY set (see .env.example / README.md)
"""

import sys

from PyQt5.QtWidgets import QApplication

from ui.floating_window import FloatingWindow


def main():
    app = QApplication(sys.argv)
    # Quitting the floating window shouldn't be treated as "quitting the
    # app" in some edge cases on certain platforms; explicit quit-on-close
    # keeps behavior predictable across Windows/macOS/Linux.
    app.setQuitOnLastWindowClosed(True)

    window = FloatingWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
