@echo off
REM packaging\build_windows.bat
REM -----------------------------
REM Builds a standalone "DiagramTutor.exe" that someone can double-click
REM to run, with no Python, pip, or source files of their own required.
REM
REM Run this ON A WINDOWS MACHINE (PyInstaller builds for whatever OS it
REM runs on - it cannot cross-compile a Windows .exe from a Mac or Linux
REM box). This matches NFR-18's stated primary platform.
REM
REM Usage (from the project root, i.e. the diagram-tutor\ folder, in a
REM Command Prompt or PowerShell window):
REM   packaging\build_windows.bat
REM
REM What this still does NOT bundle (see README.md "Distributing the app"):
REM   - Ollama itself, or the qwen3:4b model - the recipient installs that
REM     once, separately, the same way you did.
REM   - A Claude API key - each recipient supplies their own via a .env
REM     file placed next to the built app (NOT baked into the executable).

echo Installing PyInstaller (if not already installed)...
pip install pyinstaller
if errorlevel 1 goto :error

REM Only bundle the local Mermaid.js copy if it exists (created earlier
REM via the curl command in README.md). If it's missing, the app still
REM builds fine and just falls back to loading Mermaid from the CDN.
set EXTRA_DATA_ARG=
if exist "utils\vendor\mermaid.min.js" (
    set EXTRA_DATA_ARG=--add-data "utils\vendor;utils\vendor"
) else (
    echo Note: utils\vendor\mermaid.min.js not found - skipping local bundle, app will use the CDN copy instead.
)

echo Building DiagramTutor.exe...
pyinstaller --name "DiagramTutor" --windowed --noconfirm --clean %EXTRA_DATA_ARG% main.py
if errorlevel 1 goto :error

echo.
echo Done. Your app is at: dist\DiagramTutor\DiagramTutor.exe
echo.
echo To distribute it:
echo   1. Copy the whole dist\DiagramTutor folder (PyInstaller's default
echo      Windows build is a folder, not a single file - don't just copy
echo      the .exe alone, it needs the files next to it).
echo   2. Copy .env.example into that folder, rename it to .env, and have
echo      the recipient fill in their own ANTHROPIC_API_KEY.
echo   3. Zip the folder and send it. The recipient still needs to install
echo      Ollama + pull qwen3:4b themselves (see README.md).
goto :eof

:error
echo Build failed - see the error above.
exit /b 1
