"""
utils/config.py
-----------------
Loads configuration (right now, just the Claude API key) from a local
.env file using python-dotenv.

Covers:
    NFR-13: the Claude API key is stored in .env and never hard-coded
    NFR-20: Ollama itself isn't configured here - it's just expected to be
            running locally; see README.md for setup instructions.

Beginner notes:
    A ".env" file is a plain text file with KEY=VALUE lines, e.g.:
        ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
    python-dotenv reads that file and loads the values as if they were
    normal operating-system environment variables, which keeps secrets out
    of the source code (and out of git, since .env is in .gitignore).

Packaged-app note:
    When running from source with `python main.py`, python-dotenv's
    default load_dotenv() finds ".env" by searching upward from the
    current working directory - that works fine as long as you run the
    command from the project root.

    But once this app is bundled into a standalone executable (PyInstaller,
    for distributing to someone who doesn't have Python installed), there
    IS no "project root" anymore, and the working directory when someone
    double-clicks the app is unpredictable. So for a frozen/packaged build,
    we instead look for ".env" sitting right next to the executable itself
    - that's the file a recipient is expected to edit with their own
    Claude API key before launching the app (see README.md's distribution
    section).
"""

import os
import sys

from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    # Running as a PyInstaller-built executable. sys.executable points at
    # the actual .exe / app binary, so its directory is where we expect a
    # recipient to have placed their own .env file alongside it.
    _app_dir = os.path.dirname(os.path.abspath(sys.executable))
    load_dotenv(os.path.join(_app_dir, ".env"))
else:
    # Running from source (`python main.py`) - default behavior, searches
    # the current directory and its parents for a ".env" file.
    load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Centralizing the model name here means a future model upgrade only
# requires changing one line.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")


def has_claude_api_key() -> bool:
    """Used by claude_client.py to fail fast with a friendly message
    instead of letting a confusing SDK error bubble up to the user."""
    return bool(ANTHROPIC_API_KEY)
