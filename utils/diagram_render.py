"""
utils/diagram_render.py
-------------------------
Renders the diagram code returned by Claude (core/claude_client.py) inside
the chat panel.

Covers:
    FR-23: Mermaid diagrams render via Mermaid.js inside a Qt WebEngine view
    FR-24: SVG diagrams render directly inside the chat panel
    FR-25: diagrams scale appropriately when the panel is resized
    plus graceful fallback if Mermaid fails to parse (mentioned in the
    team checklist: "Handle render errors gracefully")

Beginner notes:
    - PyQt5 can't natively understand Mermaid syntax - Mermaid is a
      JavaScript library that runs in a browser-like environment. So we
      build a tiny HTML page that loads Mermaid.js from a CDN, hand it the
      diagram text, and display that HTML page inside a QWebEngineView
      (a mini embedded Chromium browser widget).
    - SVG is just XML, so Qt's QSvgWidget can draw it directly - no browser
      engine needed, which is lighter-weight.
"""

import os
import tempfile

from PyQt5.QtCore import Qt, QByteArray, QUrl
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtSvg import QSvgWidget

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView

    WEB_ENGINE_AVAILABLE = True
except ImportError:
    # If PyQtWebEngine isn't installed yet, Mermaid rendering degrades to
    # a friendly placeholder instead of crashing the whole app.
    WEB_ENGINE_AVAILABLE = False


# ---------------------------------------------------------------------------
# Mermaid.js source: prefer a locally bundled copy (no network dependency,
# faster, and more reliable than a CDN - some corporate/home networks or
# firewalls silently block CDN requests made from inside QtWebEngine, which
# causes diagrams to show raw, un-rendered Mermaid text instead of a chart).
#
# To bundle it locally:
#   1. Create a "vendor" folder next to this file's parent (utils/vendor/)
#   2. Download mermaid.min.js into it, e.g.:
#        curl -L -o utils/vendor/mermaid.min.js \
#          https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js
# If that file isn't present, we fall back to loading from a CDN.
# ---------------------------------------------------------------------------
_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
_LOCAL_MERMAID_PATH = os.path.join(_UTILS_DIR, "vendor", "mermaid.min.js")
_CDN_MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"


def _mermaid_script_src() -> str:
    if os.path.isfile(_LOCAL_MERMAID_PATH):
        return QUrl.fromLocalFile(_LOCAL_MERMAID_PATH).toString()
    return _CDN_MERMAID_URL


# A minimal HTML page that loads Mermaid.js (local file or CDN, see above)
# and renders one diagram. `{diagram_code}` / `{mermaid_src}` are
# substituted in at render time. The window.onerror + script.onerror
# handlers surface load/parse failures as a visible message instead of
# silently leaving the raw, un-rendered Mermaid text on screen.
MERMAID_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  body {{
    margin: 0;
    background-color: #23242c;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: sans-serif;
  }}
  #diagram {{
    width: 100%;
  }}
  .error {{
    color: #e35d6a;
    padding: 12px;
  }}
</style>
</head>
<body>
  <div id="diagram" class="mermaid">{diagram_code}</div>
  <div id="error-box" class="error" style="display:none;"></div>
  <script>
    function showError(msg) {{
      document.getElementById("diagram").style.display = "none";
      var box = document.getElementById("error-box");
      box.style.display = "block";
      box.innerText = msg;
    }}
    // TEMP DEBUG MODE: showing the real error text (instead of a generic
    // message) so we can see exactly what's failing. We'll quiet this
    // back down once rendering is confirmed working.
    window.onerror = function (msg, src, line, col, err) {{
      showError("JS error: " + msg + " (line " + line + ")");
    }};

    // Polyfill: QtWebEngine 5.15 bundles an older Chromium that predates
    // structuredClone() (added in Chromium 98 / Node 17), but Mermaid v10
    // calls it internally. This JSON-based fallback covers Mermaid's
    // plain-object use case (it doesn't need to handle functions, DOM
    // nodes, or circular references here).
    if (typeof structuredClone !== "function") {{
      window.structuredClone = function (obj) {{
        return JSON.parse(JSON.stringify(obj));
      }};
    }}

    // Polyfill: Object.hasOwn (added in Chromium 93 / ES2022) - another
    // modern JS feature Mermaid v10 uses internally that this older
    // bundled browser doesn't have natively.
    if (typeof Object.hasOwn !== "function") {{
      Object.hasOwn = function (obj, prop) {{
        return Object.prototype.hasOwnProperty.call(obj, prop);
      }};
    }}

    var script = document.createElement("script");
    script.src = "{mermaid_src}";
    script.onload = function () {{
      try {{
        mermaid.initialize({{ startOnLoad: false, theme: "dark" }});
        mermaid.run({{ querySelector: ".mermaid" }}).catch(function (err) {{
          showError("Mermaid render error: " + (err && err.message ? err.message : err));
        }});
      }} catch (e) {{
        showError("Mermaid threw: " + (e && e.message ? e.message : e));
      }}
    }};
    script.onerror = function () {{
      showError("Couldn't load the diagram renderer script (path: {mermaid_src}).");
    }};
    document.head.appendChild(script);
  </script>
</body>
</html>
"""


class MermaidRenderer(QWidget):
    """
    Renders a Mermaid diagram string using Mermaid.js inside an embedded
    QWebEngineView (FR-23).
    """

    def __init__(self, mermaid_code: str, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if not WEB_ENGINE_AVAILABLE:
            # Graceful fallback (mirrors the "render errors" requirement):
            # show the raw Mermaid code rather than failing silently.
            fallback = QLabel(
                "Diagram preview unavailable - install PyQtWebEngine "
                "(pip install PyQtWebEngine) to see rendered diagrams.\n\n"
                f"{mermaid_code}"
            )
            fallback.setObjectName("DiagramPlaceholder")
            fallback.setWordWrap(True)
            layout.addWidget(fallback)
            return

        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(220)
        # FR-25: QWebEngineView already scales its contents with the
        # widget's size because the layout above is Expanding; the HTML
        # itself uses width: 100% so Mermaid's SVG output stretches too.
        html = MERMAID_HTML_TEMPLATE.format(
            diagram_code=_escape_for_html(mermaid_code),
            mermaid_src=_mermaid_script_src(),
        )
        # Loading via setHtml() gives the page a null/about:blank origin,
        # and Chromium refuses to let pages with that origin load local
        # file:// resources (security restriction) - this is what caused
        # the local Mermaid bundle to silently fail to load. Writing the
        # page to a real temp .html file and loading THAT gives it a
        # genuine file:// origin, which IS allowed to load other local
        # files (like utils/vendor/mermaid.min.js) sitting next to it.
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".html", prefix="diagram_tutor_")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(html)
        self._tmp_html_path = tmp_path
        self.web_view.load(QUrl.fromLocalFile(tmp_path))
        layout.addWidget(self.web_view)

    def resizeEvent(self, event):
        # Re-rendering on every resize keeps the diagram crisp at any
        # panel size (FR-25). Mermaid + CSS width:100% already mostly
        # handles this, but forcing a relayout avoids stale clipping.
        super().resizeEvent(event)
        if WEB_ENGINE_AVAILABLE and hasattr(self, "web_view"):
            self.web_view.resize(self.size())


class SVGRenderer(QWidget):
    """
    Renders a standalone SVG string directly inside the chat panel
    (FR-24), using Qt's lightweight native SVG widget.
    """

    def __init__(self, svg_code: str, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.svg_widget = QSvgWidget()
        try:
            self.svg_widget.load(QByteArray(svg_code.encode("utf-8")))
            if not self.svg_widget.renderer().isValid():
                raise ValueError("Invalid SVG markup")
            layout.addWidget(self.svg_widget)
        except Exception:
            # Render-error fallback: show a placeholder instead of a blank
            # or broken widget.
            fallback = QLabel("Couldn't render this SVG diagram.")
            fallback.setObjectName("DiagramPlaceholder")
            fallback.setWordWrap(True)
            layout.addWidget(fallback)

    def resizeEvent(self, event):
        # FR-25: keep the SVG's aspect-correct scaling in sync with the
        # widget's current size on every resize.
        super().resizeEvent(event)
        if hasattr(self, "svg_widget"):
            self.svg_widget.setFixedSize(self.size())


class DiagramLoadingPlaceholder(QLabel):
    """
    Simple "Generating diagram..." placeholder shown while Claude is
    working (FR-22). Swapped out for a MermaidRenderer/SVGRenderer once
    the diagram is ready, or for an error message on failure.
    """

    def __init__(self, parent=None):
        super().__init__("⏳ Generating diagram...", parent)
        self.setObjectName("DiagramPlaceholder")
        self.setAlignment(Qt.AlignCenter)


def build_diagram_widget(diagram_type: str, diagram_code: str, parent=None) -> QWidget:
    """
    Factory used by chat_panel.py: given Claude's chosen type, return the
    right renderer widget. Keeps chat_panel.py decoupled from renderer
    implementation details.
    """
    if diagram_type == "mermaid":
        return MermaidRenderer(diagram_code, parent)
    elif diagram_type == "svg":
        return SVGRenderer(diagram_code, parent)
    else:
        fallback = QLabel(f"Unsupported diagram type: {diagram_type}")
        fallback.setObjectName("DiagramPlaceholder")
        return fallback


def _escape_for_html(mermaid_code: str) -> str:
    """Prevents Mermaid source text from accidentally closing the
    surrounding <div> if it contains literal '<' or '>' characters."""
    return mermaid_code.replace("<", "&lt;").replace(">", "&gt;").replace(
        "&lt;br&gt;", "<br>"  # allow Mermaid's common <br> line-break syntax
    )
