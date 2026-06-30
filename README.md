# Diagram Tutor

A floating, always-on-top desktop widget that explains any topic through
text and auto-generated visual diagrams. It combines a locally-running
Ollama model (text explanations) with the Claude API (diagram generation),
rendered live in a small panel that sits on top of whatever you're working
in - a browser, a PDF, a video.

## How it works

1. You ask a question in the chat panel.
2. The question goes to a local Ollama model (`qwen3:4b`), which answers in
   plain text and, when a visual would help, appends a tag like
   `[DIAGRAM: lifecycle of an HTTP request]`.
3. If that tag is present, the description is sent to the Claude API, which
   decides whether a Mermaid diagram (flowchart, timeline, sequence, mind
   map) or a small SVG illustration best represents the concept.
4. The diagram is rendered directly inside the chat panel, below the
   explanation.

## Project structure

```
diagram-tutor/
├── main.py                  # entry point
├── requirements.txt
├── .env.example             # copy to .env and add your Claude API key
├── ui/
│   ├── floating_window.py   # frameless, always-on-top, draggable/resizable panel
│   ├── chat_panel.py        # bubbles, input box, typing indicator, diagram area
│   └── styles.py            # dark theme + hover/focus states
├── core/
│   ├── ollama_client.py     # talks to local Ollama, background thread
│   └── claude_client.py     # talks to Claude API, background thread
└── utils/
    ├── diagram_render.py    # MermaidRenderer (QtWebEngine) + SVGRenderer
    └── config.py            # loads ANTHROPIC_API_KEY from .env
```

## Setup

### 1. Install Ollama (required, separate from this app)

Diagram Tutor's text explanations run entirely locally through
[Ollama](https://ollama.com), so no chat data ever leaves your machine.

1. Download and install Ollama for your OS from https://ollama.com/download
2. Pull the model this app uses:
   ```
   ollama pull qwen3:4b
   ```
3. Start the Ollama server (leave this running in the background):
   ```
   ollama serve
   ```

If you see an error like "Couldn't reach Ollama" in the app, this step is
the most common fix.

### 2. Get a Claude API key

1. Log in to the [Anthropic Console](https://console.anthropic.com)
2. Create an API key under your organization
3. Copy `.env.example` to `.env` in the project root:
   ```
   cp .env.example .env
   ```
4. Open `.env` and paste your key:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-real-key
   ```

`.env` is listed in `.gitignore` - it will never be committed to GitHub.

### 3. Install Python dependencies

Requires Python 3.9+.

```
pip install -r requirements.txt
```

> Note: `PyQtWebEngine` is what renders Mermaid diagrams. If it fails to
> install on your system, the app still runs - Mermaid diagrams will show
> a "preview unavailable" message until it's installed, but SVG diagrams
> and all chat features keep working.

### 4. Run the app

```
python main.py
```

The floating panel should appear in the bottom-right corner of your screen
within a few seconds.

## Usage

- Drag the title bar to move the panel anywhere on screen.
- Drag the bottom-right corner to resize it.
- Click the "−" button to collapse the panel to just its title bar; click
  again to restore it.
- Type a question and press Enter or click Send.
- Highlight any message text to copy it.

## Distributing the app to someone else

If you want someone to run Diagram Tutor without installing Python, pip,
or any of this source code themselves, package it into a standalone app
with PyInstaller. Two things still can't be bundled into the executable,
no matter how it's packaged, so the recipient handles these once,
themselves:

- **Ollama + the qwen3:4b model.** This is a separate local AI runtime,
  not a Python library - it has to be installed on their machine the same
  way you installed it (see Setup step 1 above). The model is a ~2.5GB
  download.
- **A Claude API key.** Each person needs their own (baking yours into
  the executable would mean you pay for everyone who runs it).

### Build it

On a Mac, from the project root:
```
bash packaging/build_mac.sh
```

On Windows (run on an actual Windows machine - PyInstaller can't
cross-compile a Windows .exe from a Mac), from the project root:
```
packaging\build_windows.bat
```

Each script installs PyInstaller if needed and produces a standalone app
in the `dist/` folder.

### What to send them

1. The built app: `dist/DiagramTutor.app` (Mac) or the whole
   `dist/DiagramTutor` folder (Windows - it's a folder, not a single file).
2. A `.env` file in the same folder as the app, with their own
   `ANTHROPIC_API_KEY` filled in (copy `.env.example`, rename it, have
   them edit it with a text editor - no terminal needed).
3. A note telling them to install Ollama and run
   `ollama pull qwen3:4b` once before first launch.

Zip the app + `.env` together and that's the whole handoff - no Python,
no `pip install`, no cloning a repo.

#### Sharing your own API key instead

If you'd rather not make each recipient get their own Claude API key (fine
for a small, trusted group like your project partner), put your real key
in the `.env` you include in step 2 above instead of leaving it blank for
them to fill in. Be aware that anyone with the app can open that `.env` in
a text editor and read the key - there's no way to hide a secret inside
software running on someone else's computer. As a safety net, set a spend
limit on that specific key in the Anthropic Console
(console.anthropic.com → Settings → Limits) so usage is capped at a known
dollar amount no matter what happens to the key after you send it.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Couldn't reach Ollama" | Run `ollama serve` in a terminal and keep it open. |
| "Ollama took too long to respond" | The model may still be loading on first use - wait a moment and retry. |
| "No Claude API key found" | Check that `.env` exists and `ANTHROPIC_API_KEY` is set correctly. |
| Diagrams don't render | Run `pip install PyQtWebEngine` and restart the app. |
| Claude rate-limit or auth errors | Check your usage/limits at console.anthropic.com. |

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| UI Framework | Python + PyQt5 | Floating window, chat bubbles, layouts |
| Local AI | Ollama (`qwen3:4b`) | Text explanations, runs fully offline |
| Diagram AI | Claude API (`claude-sonnet-4-6`) | Generates Mermaid/SVG diagram code |
| Diagram Render | Mermaid.js + PyQtWebEngine | Renders flowcharts, timelines, mind maps |
| Environment | python-dotenv + `.env` | Secure Claude API key storage |

## Status

This is a from-scratch scaffold covering the full feature set in the
product requirements doc (window/interface, chat, Ollama integration,
Claude diagram generation, and Mermaid/SVG rendering). Packaging as a
Windows `.exe` (PyInstaller) and a minimize-to-bubble animation are next.
