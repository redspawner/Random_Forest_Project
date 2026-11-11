"""Start the drag-and-drop interface and open it in the web browser.

    python run_app.py
"""

import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = "http://localhost:8501"


def _open_browser() -> None:
    time.sleep(3)
    webbrowser.open(URL)


if __name__ == "__main__":
    print(f"Starting the app at {URL}  (close this window or press Ctrl+C to stop)")
    threading.Thread(target=_open_browser, daemon=True).start()
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py")], cwd=ROOT, check=False)
    except KeyboardInterrupt:
        pass
