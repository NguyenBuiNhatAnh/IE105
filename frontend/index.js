

let serverWs = null; // Đổi tên ws thành serverWs để rõ ràng hơn
const clientWs = {}; // Dùng đối tượng để lưu trữ các kết nối client theo ID

// --- Hàm startServer (Đã cập nhật tên biến) ---
function startServer() {
    const log = document.getElementById("server-log"); // Đã cập nhật ID div log
    log.textContent += "\n[SERVER START] Connecting...\n";

    // Đảm bảo đóng kết nối cũ nếu có
    if (serverWs && serverWs.readyState !== WebSocket.CLOSED) {
        serverWs.close();
    }
    
    serverWs = new WebSocket("ws://localhost:8000/ws/logs");

    serverWs.onmessage = (event) => {
        log.textContent += event.data + "\n";
        log.scrollTop = log.scrollHeight;
    };

    serverWs.onerror = () => {
        log.textContent += "[SERVER WebSocket ERROR]\n";
    };

    serverWs.onclose = () => {
        log.textContent += "[SERVER WebSocket CLOSED]\n";
    };
}


// --- Hàm stopServer (Đã cập nhật tên biến) ---
function stopServer() {
    fetch("http://localhost:8000/stop-server", {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {
        const log = document.getElementById("server-log"); // Đã cập nhật ID div log
        log.textContent += `\n[SERVER STOP REQUEST] ${data.status}\n`;

        // nếu websocket còn mở thì đóng lại
        if (serverWs && serverWs.readyState === WebSocket.OPEN) {
            serverWs.close();
        }
    });
}

// ------------------------------------------------------------------
// --- HÀM MỚI: Khởi động Client và nhận Log qua WebSocket ---
// ------------------------------------------------------------------

function startClient(clientId) {
    // SỬA LỖI QUAN TRỌNG: Tạo ID DIV động từ clientId (ví dụ: client-log-1)
    const logDivId = `client-log-${clientId}`;
    const clientLogDiv = document.getElementById(logDivId); 
    
    // Kiểm tra xem div có tồn tại không
    if (!clientLogDiv) {
        console.error(`Không tìm thấy div log với ID: ${logDivId}`);
        return; 
    }

    const endpoint = `ws://localhost:8000/ws/client/${clientId}/logs`;

    clientLogDiv.textContent += `\n[CLIENT ${clientId} START] Đang kết nối đến ${endpoint}...\n`;

    // 1. Kiểm tra nếu Client này đã có kết nối đang mở
    if (clientWs[clientId] && clientWs[clientId].readyState === WebSocket.OPEN) {
        clientLogDiv.textContent += `[CLIENT ${clientId}] Đã có kết nối đang hoạt động.\n`;
        return;
    }
    
    // Đóng kết nối cũ nếu nó ở trạng thái khác
    if (clientWs[clientId]) {
         clientWs[clientId].close();
    }

    // 2. Tạo kết nối WebSocket mới
    const ws = new WebSocket(endpoint);
    clientWs[clientId] = ws; // Lưu kết nối vào đối tượng global

    // 3. Xử lý tin nhắn
    ws.onmessage = (event) => {
        // Hiển thị log
        clientLogDiv.textContent += `[C${clientId}] ${event.data}\n`;
        clientLogDiv.scrollTop = clientLogDiv.scrollHeight;
    };

    // 4. Xử lý lỗi
    ws.onerror = () => {
        clientLogDiv.textContent += `[CLIENT ${clientId} ERROR] Lỗi WebSocket (Kiểm tra backend đã chạy chưa).\n`;
    };

    // 5. Xử lý đóng kết nối
    ws.onclose = () => {
        clientLogDiv.textContent += `[CLIENT ${clientId} CLOSED] Kết nối đã đóng.\n`;
        delete clientWs[clientId];
    };
}