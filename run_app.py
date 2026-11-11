"""Start the drag-and-drop interface and open it in the web browser once it is ready.

    python run_app.py            # opens the browser automatically
    python run_app.py --no-browser

The browser is opened only after the app answers (the first start of the portable Windows
version can take a minute while the antivirus scans the files). If port 8501 is busy, the
next free port is used. The app listens on 127.0.0.1 only (this computer).
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
FIRST_PORT = 8501
STARTUP_TIMEOUT = 240     # seconds


def free_port(start: int = FIRST_PORT) -> int:
    """First port that can be reserved on this computer (instant local check, cannot hang)."""
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((HOST, port))
            except OSError:          # already in use (e.g. the app is open in another window)
                continue
            return port
    raise RuntimeError("No free port found between 8501 and 8550.")


def is_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url + "/_stcore/health", timeout=2) as response:
            return response.status == 200
    except OSError:
        return False


def main() -> int:
    open_browser = "--no-browser" not in sys.argv
    port = free_port()
    url = f"http://{HOST}:{port}"
    if port != FIRST_PORT:
        print(f"Port {FIRST_PORT} is busy (is the app already open in another window?). Using port {port}.", flush=True)
    print("Starting the app... the first start can take up to a minute.", flush=True)
    print("Keep this window open while you use the app. Close it (or press Ctrl+C) to stop.\n", flush=True)
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
         "--server.address", HOST, "--server.port", str(port), "--server.headless", "true"],
        cwd=ROOT,
    )
    start = time.time()
    try:
        while not is_ready(url):
            if process.poll() is not None:
                print("\nERROR: the app stopped while starting (see the messages above).", flush=True)
                return 1
            if time.time() - start > STARTUP_TIMEOUT:
                print(f"\nThe app is taking unusually long. Try opening {url} in your browser yourself.", flush=True)
                break
            time.sleep(1)
        else:
            print(f"\n==> The app is ready: {url}  ({time.time() - start:.0f} s)", flush=True)
            if open_browser:
                webbrowser.open(url)
            else:
                print("    Open that address in your web browser.", flush=True)
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return 0


if __name__ == "__main__":
    sys.exit(main())
