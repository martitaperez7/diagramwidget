#!/bin/bash
# packaging/build_mac.sh
# ------------------------
# Builds a standalone "DiagramTutor.app" that someone can double-click to
# run, with no Python, pip, or source files of their own required.
#
# Run this ON A MAC (PyInstaller builds for whatever OS it runs on - it
# cannot cross-compile a Windows .exe from here. See build_windows.bat for
# the Windows equivalent).
#
# Usage (from the project root, i.e. the diagram-tutor/ folder):
#   bash packaging/build_mac.sh
#
# What this still does NOT bundle (see README.md "Distributing the app"):
#   - Ollama itself, or the qwen3:4b model - the recipient installs that
#     once, separately, the same way you did.
#   - A Claude API key - each recipient supplies their own via a .env
#     file placed next to the built app (NOT baked into the executable).

set -e  # stop immediately if any command fails

echo "Installing PyInstaller (if not already installed)..."
pip3 install --quiet pyinstaller

# Only bundle the local Mermaid.js copy if it exists (created earlier via
# the curl command in README.md). If it's missing, the app still builds
# fine and just falls back to loading Mermaid from the CDN at runtime.
EXTRA_DATA_ARGS=()
if [ -f "utils/vendor/mermaid.min.js" ]; then
  EXTRA_DATA_ARGS+=(--add-data "utils/vendor:utils/vendor")
else
  echo "Note: utils/vendor/mermaid.min.js not found - skipping local bundle, app will use the CDN copy instead."
fi

echo "Building DiagramTutor.app..."
pyinstaller \
  --name "DiagramTutor" \
  --windowed \
  --noconfirm \
  --clean \
  "${EXTRA_DATA_ARGS[@]}" \
  main.py

echo ""
echo "Done. Your app is at: dist/DiagramTutor.app"
echo ""
echo "To distribute it:"
echo "  1. Copy dist/DiagramTutor.app into a new folder."
echo "  2. Copy .env.example into that same folder, rename it to .env,"
echo "     and have the recipient fill in their own ANTHROPIC_API_KEY."
echo "  3. Zip that folder and send it. The recipient still needs to"
echo "     install Ollama + pull qwen3:4b themselves (see README.md)."
