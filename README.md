# 🧠 Visual Study Assistant

A floating always-on-top desktop widget that helps visual learners
understand any topic through AI-generated diagrams and explanations.

---

## 🚀 Setup & Run

### 1. Make sure Python is installed
Download from https://www.python.org (version 3.9 or higher)

### 2. Install dependencies
Open a terminal in this folder and run:
```
pip install -r requirements.txt
```

### 3. Run the app
```
python main.py
```

---

## 🗂️ Project Structure

```
visual-study-assistant/
├── main.py                  ← Run this to launch the app
├── requirements.txt         ← Python packages needed
├── ui/
│   └── floating_window.py   ← Floating window UI (Step 1 ✅)
├── core/
│   ├── ollama_client.py     ← Ollama AI responses (Step 3)
│   └── claude_client.py     ← Claude diagram generation (Step 4)
└── utils/
    └── diagram_render.py    ← Mermaid/SVG renderer (Step 5)
```

---

## ✅ Build Progress

- [x] Step 1 — Floating always-on-top window (draggable + resizable)
- [ ] Step 2 — Chat UI polish
- [ ] Step 3 — Ollama integration
- [ ] Step 4 — Claude diagram generation
- [ ] Step 5 — Diagram rendering
- [ ] Step 6 — Minimize to bubble + polish

---

## ⌨️ Controls

| Action | How |
|--------|-----|
| Move | Drag the title bar |
| Resize | Drag the bottom-right corner grip |
| Minimize | Click the **─** button |
| Close | Click the **✕** button |