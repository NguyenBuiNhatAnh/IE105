import asyncio
import threading
import subprocess
from fastapi import FastAPI, WebSocket
import sys
from queue import Queue

app = FastAPI()

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    q = Queue()

    # Python của venv
    python_exe = sys.executable

    # Thread chạy server.py và đẩy log vào queue
    def run_server_and_stream():
        process = subprocess.Popen(
            [python_exe, "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            if line:
                q.put(line.strip())

        q.put("[SERVER STOPPED]")

    threading.Thread(target=run_server_and_stream, daemon=True).start()

    # Task async gửi log về client
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, q.get)
            await websocket.send_text(line)
            if line == "[SERVER STOPPED]":
                break
    except Exception:
        pass

    await websocket.close()
