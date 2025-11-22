function startServer() {
    const ws = new WebSocket("ws://localhost:8000/ws/logs");
    const log = document.getElementById("log");

    ws.onmessage = (event) => {
        log.textContent += event.data + "\n";
        log.scrollTop = log.scrollHeight;
    };

    ws.onerror = () => {
        log.textContent += "[WebSocket error]\n";
    };

    ws.onclose = () => {
        log.textContent += "[WebSocket closed]\n";
    };
}