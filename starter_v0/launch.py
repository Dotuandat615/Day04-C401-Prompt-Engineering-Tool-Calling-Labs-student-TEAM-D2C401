# -*- coding: utf-8 -*-
"""
Launcher: start Streamlit + ngrok tunnel for public sharing.
Usage: python launch.py
"""
import subprocess
import sys
import time
import threading
import os

os.environ["PYTHONIOENCODING"] = "utf-8"

PORT = 8501

def start_ngrok():
    try:
        from pyngrok import ngrok
        tunnel = ngrok.connect(PORT, "http")
        public_url = tunnel.public_url
        print("\n" + "="*60)
        print("SHARE LINK (Public ngrok URL):")
        print(f"   >> {public_url}")
        print("="*60)
        print("\nCopy URL tren de chia se voi nguoi khac!")
        print("   (Link het han khi ban tat script nay)\n")
        return public_url
    except Exception as e:
        print(f"\nngrok tunnel error: {e}")
        print("   Dung localhost:{PORT} thay the.\n")
        return None

if __name__ == "__main__":
    print("Starting Research Agent UI...")

    def delayed_ngrok():
        time.sleep(4)
        start_ngrok()

    t = threading.Thread(target=delayed_ngrok, daemon=True)
    t.start()

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
        ])
    except KeyboardInterrupt:
        print("\nApp stopped.")
