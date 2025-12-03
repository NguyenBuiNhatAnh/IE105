import flwr as fl
from flwr.server.strategy import FedAvg
from task import SimpleCNN, ImprovedCNN
import argparse 


# Khởi tạo mô hình toàn cục
model = SimpleCNN()
initial_parameters = fl.common.ndarrays_to_parameters(
    [val.cpu().numpy() for _, val in model.state_dict().items()]
)

def evaluate_config(server_round: int):
    return {
        "server_round": server_round,
    }

if __name__ == "__main__":
    # 1. Định nghĩa và đọc đối số dòng lệnh
    parser = argparse.ArgumentParser(description="Flower Server.")
    
    # Thêm tham số num_rounds
    parser.add_argument(
        "--num_rounds",
        type=int,
        default=100,
        help="Số vòng huấn luyện (mặc định: 100)",
    )
    
    # 👈 Thêm tham số learning rate (lr)
    parser.add_argument(
        "--lr",
        type=float, # Dùng float vì lr là số thực
        default=0.01, # Giá trị mặc định
        help="Tốc độ học (Learning Rate) cho client (mặc định: 0.01)",
    )

    parser.add_argument(
        "--local_epochs",
        type=int,
        default=1, # Giá trị mặc định
    )
    
    args = parser.parse_args()
    
    # Lấy giá trị num_rounds
    num_rounds = args.num_rounds
    
    # 👈 Lấy giá trị lr và gán vào biến toàn cục
    global_lr = args.lr

    local_epochs = args.local_epochs

    def fit_config(server_round: int):
        return {
            "server_round": server_round,
            "local_epochs": local_epochs,
            # Sử dụng biến GLOBAL_LR đã được thiết lập
            "lr": global_lr, 
        }
    
    print(f"[SERVER] Starting with config:", flush=True)
    print(f"  - num_rounds = {num_rounds}", flush=True)
    print(f"  - lr = {global_lr}", flush=True)
    print(f"  - local_epochs = {local_epochs}", flush=True)

    # 2. Khởi động server
    fl.server.start_server(
        server_address="localhost:8080",
        config=fl.server.ServerConfig(num_rounds=num_rounds), 
        strategy=FedAvg(
            initial_parameters=initial_parameters,
            min_available_clients=2,
            min_fit_clients=2,
            min_evaluate_clients=2,
            on_fit_config_fn=fit_config,
            on_evaluate_config_fn=evaluate_config,
        ),
    )