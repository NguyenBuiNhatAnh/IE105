let ws = null;

function startServer() {
    const log = document.getElementById("log");
    log.textContent += "\n[START] Connecting...\n";

    ws = new WebSocket("ws://localhost:8000/ws/logs");

    ws.onmessage = (event) => {
        log.textContent += event.data + "\n";
        log.scrollTop = log.scrollHeight;
    };

    ws.onerror = () => {
        log.textContent += "[WebSocket ERROR]\n";
    };

    ws.onclose = () => {
        log.textContent += "[WebSocket CLOSED]\n";
    };
}

function stopServer() {
    // gọi API backend
    fetch("http://localhost:8000/stop-server", {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {
        const log = document.getElementById("log");
        log.textContent += `\n[STOP REQUEST] ${data.status}\n`;

        // nếu websocket còn mở thì đóng lại
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }
    });
}
