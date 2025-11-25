

import sys
import torch
import flwr as fl
from task import SimpleCNN, ImprovedCNN, load_data, train as train_fn, test as test_fn
import requests

class FlowerClient(fl.client.NumPyClient):
    def __init__(self, partition_id):
        self.partition_id = partition_id
        self.model = SimpleCNN()
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.trainloader, self.valloader = load_data(partition_id)

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        state_dict = dict(zip(self.model.state_dict().keys(), [torch.tensor(p) for p in parameters]))
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        train_fn(
            self.model,
            self.trainloader,
            epochs=int(config.get("local_epochs", 1)),
            lr=float(config.get("lr", 0.011)),
            device=self.device,
        )
        return self.get_parameters(config), len(self.trainloader.dataset), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, acc = test_fn(self.model, self.valloader, self.device)
        round_num = config.get("server_round", "Unknown")

        print(f"[Client {self.partition_id}] Round {round_num} - Evaluation - Loss: {loss:.4f}, Accuracy: {acc:.2f}%", flush=True)

        if(self.partition_id == 1):
            try:
                requests.post(
                    "http://localhost:8000/client/metric",
                    json={
                        "round": round_num,
                        "acc": float(acc)
                    }
                )
            except Exception as e:
                print("[Client] Failed to POST acc:", e)

        return float(loss), len(self.valloader.dataset), {"accuracy": float(acc)}


if __name__ == "__main__":
    partition_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    fl.client.start_numpy_client(server_address="localhost:8080", client=FlowerClient(partition_id))