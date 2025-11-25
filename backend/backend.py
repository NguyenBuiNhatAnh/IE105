# backend.py
import asyncio
import threading
import subprocess
import sys
from queue import Queue, Empty
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi import Path
from typing import Dict
import json

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
        

# Khởi tạo các biến/lock/app nếu chưa có
process_lock = threading.Lock()
# Sử dụng Dict để lưu trữ các process theo client_id
running_processes: Dict[int, subprocess.Popen] = {} 

@app.websocket("/ws/client/{client_id}/logs")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: int = Path(..., description="ID của client để chạy")
):
    await websocket.accept()
    q = Queue()
    python_exe = sys.executable

    # Hàm chạy client.py với ID
    def run_client_and_stream(client_id: int):
        # Tạo key duy nhất cho process này
        process_key = client_id
        
        with process_lock:
            # 1. Kiểm tra nếu process với ID này đã chạy
            if process_key in running_processes and running_processes[process_key].poll() is None:
                q.put(f"[CLIENT_ID_{client_id}_ALREADY_RUNNING]")
                return
            
            # 2. Khởi tạo process mới
            process = subprocess.Popen(
                [python_exe, "client.py", str(client_id)], # <-- THAY ĐỔI CHÍNH Ở ĐÂY
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            running_processes[process_key] = process # Lưu process vào Dict

        # Đọc stdout của tiến trình
        try:
            for line in process.stdout:
                if line:
                    q.put(line.rstrip("\n"))
        except Exception:
            pass
        finally:
            q.put(f"[CLIENT_ID_{client_id}_STOPPED]")
            # Dọn dẹp process khi nó dừng
            with process_lock:
                if process_key in running_processes:
                    del running_processes[process_key]

    # Start thread (daemon) để chạy client.py
    threading.Thread(target=run_client_and_stream, args=(client_id,), daemon=True).start()

    try:
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: q.get(timeout=0.2)
                )
            except Empty:
                await asyncio.sleep(0)
                continue

            try:
                await websocket.send_text(line)
            except Exception:
                break

            if line.endswith("_STOPPED]"):
                break

    except asyncio.CancelledError:
        # Xử lý khi WebSocket bị cancel: Kill tiến trình con
        with process_lock:
            process = running_processes.get(client_id)
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=3)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass
                finally:
                    # Dọn dẹp process
                    if client_id in running_processes:
                        del running_processes[client_id]
        raise
    finally:
        await websocket.close()

accclient = []
wsclient1acc = None

@app.post("/client/metric")
async def recieve(data: dict):
    global accclient, wsclient1acc
    accclient.append(data)

    # Nếu WebSocket đang kết nối thì gửi dữ liệu
    if wsclient1acc is not None:
        try:
            await wsclient1acc.send_text(json.dumps(data))
        except:
            wsclient1acc = None  # reset nếu WS đóng

    return {"status": "ok"}


@app.websocket("/ws/client/acc")
async def sendacc(websocket: WebSocket):
    global wsclient1acc
    await websocket.accept()
    wsclient1acc = websocket
    print("WebSocket Client 1 connected")

    try:
        while True:
            await websocket.receive_text()  # giữ kết nối
    except:
        wsclient1acc = None
        print("WebSocket Client 1 disconnected")