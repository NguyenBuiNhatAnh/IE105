# backend.py
import asyncio
import threading
import subprocess
import sys
from queue import Queue, Empty
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

app = FastAPI()

# Biến toàn cục giữ tiến trình server.py
server_process = None
process_lock = threading.Lock()  # để tránh race khi start/stop


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    global server_process

    await websocket.accept()
    q = Queue()

    python_exe = sys.executable

    # Thread chạy server.py và đẩy log vào queue
    def run_server_and_stream():
        global server_process
        with process_lock:
            # nếu đã có process đang chạy thì không start lại
            if server_process and server_process.poll() is None:
                q.put("[SERVER_ALREADY_RUNNING]")
                return

            server_process = subprocess.Popen(
                [python_exe, "server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

        # Đọc stdout của tiến trình
        try:
            for line in server_process.stdout:
                if line:
                    q.put(line.rstrip("\n"))
        except Exception:
            pass
        finally:
            q.put("[SERVER STOPPED]")

    # Start thread (daemon) để chạy server.py
    threading.Thread(target=run_server_and_stream, daemon=True).start()

    try:
        while True:
            try:
                # Không block vô hạn — timeout để loop có thể kiểm tra cancel
                line = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: q.get(timeout=0.2)
                )
            except Empty:
                # kiểm tra websocket vẫn mở, sau đó lặp lại
                await asyncio.sleep(0)  # yield control
                continue

            # gửi log cho client
            try:
                await websocket.send_text(line)
            except Exception:
                # client có thể đóng kết nối bất ngờ
                break

            if line == "[SERVER STOPPED]":
                break

    except asyncio.CancelledError:
        # WebSocket bị cancel (ví dụ reload or Ctrl+C) -> dọn dẹp process
        with process_lock:
            if server_process and server_process.poll() is None:
                try:
                    server_process.terminate()
                    server_process.wait(timeout=3)
                except Exception:
                    try:
                        server_process.kill()
                    except Exception:
                        pass
        raise
    finally:
        await websocket.close()


@app.post("/stop-server")
async def stop_server():
    """HTTP endpoint để dừng server.py một cách an toàn"""
    global server_process
    with process_lock:
        if server_process and server_process.poll() is None:
            try:
                server_process.terminate()  # gửi SIGTERM (Windows: TerminateProcess)
                try:
                    server_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # không dừng -> kill cứng
                    server_process.kill()
                return JSONResponse({"status": "terminated"})
            except Exception as e:
                return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
        else:
            return JSONResponse({"status": "not running"})
