import sys
import os
import argparse
import subprocess
import threading
import time
import signal
import atexit

def start_api():
    subprocess.run([sys.executable, "-m", "uvicorn", "src.pwcproject.api:app", "--host", "0.0.0.0", "--port", "8000"])

def start_streamlit():
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/pwcproject/streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"])

if __name__ == "__main__":
    print("Starting GPT-4 Data Analyst Application...")
    print("API: http://localhost:8000")
    print("Web: http://localhost:8501")
    
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    time.sleep(2)
    start_streamlit()
