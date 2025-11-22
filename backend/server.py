import flwr as fl
from flwr.server.strategy import FedAvg
from task import SimpleCNN
import logging
import sys

# Cấu hình logging để đẩy log ra stdout
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True  # Ghi đè cấu hình mặc định của Flower
)

logging.info("Starting Flower server...")

# Khởi tạo mô hình toàn cục
model = SimpleCNN()
initial_parameters = fl.common.ndarrays_to_parameters(
    [val.cpu().numpy() for _, val in model.state_dict().items()]
)

# Hàm truyền config cho client khi huấn luyện
def fit_config(server_round: int):
    return {
        "server_round": server_round,
        "local_epochs": 5,
        "lr": 1,
    }

# Hàm truyền config cho client khi đánh giá
def evaluate_config(server_round: int):
    return {
        "server_round": server_round,
    }

# Khởi động server
fl.server.start_server(
    server_address="localhost:8080",
    config=fl.server.ServerConfig(num_rounds=50),
    strategy=FedAvg(
        initial_parameters=initial_parameters,
        min_available_clients=3,
        min_fit_clients=3,
        min_evaluate_clients=3,
        on_fit_config_fn=fit_config,
        on_evaluate_config_fn=evaluate_config,
    ),
)