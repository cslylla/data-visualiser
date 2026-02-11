import subprocess
import sys
import time
import webbrowser
import socket


def wait_for_port(host: str, port: int, timeout_s: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def main() -> int:
    # Start Streamlit
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py"])

    # Wait until it's up, then open browser
    if wait_for_port("127.0.0.1", 8501, timeout_s=20):
        webbrowser.open("http://localhost:8501")

    return proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
