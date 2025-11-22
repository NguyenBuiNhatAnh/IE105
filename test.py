import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms



def load_data(id):
    transform = transforms.Compose([transforms.Grayscale(), 
                                transforms.Resize((64, 64)), 
                                transforms.ToTensor()])
    
    if(id == 1):
        dataset = torchvision.datasets.ImageFolder(root='./client1', transform=transform)
    elif(id == 2):
        dataset = torchvision.datasets.ImageFolder(root='./client2', transform=transform)
    elif(id == 3):
        dataset = torchvision.datasets.ImageFolder(root='./client3', transform=transform)
    elif(id == 4):
        dataset = torchvision.datasets.ImageFolder(root='./client4', transform=transform)
    elif(id == 5):
        dataset = torchvision.datasets.ImageFolder(root='./client5', transform=transform)
    elif(id == 6):
        dataset = torchvision.datasets.ImageFolder(root='./client6', transform=transform)
    elif(id == 7):
        dataset = torchvision.datasets.ImageFolder(root='./client7', transform=transform)
    elif(id == 8):
        dataset = torchvision.datasets.ImageFolder(root='./client8', transform=transform)
    else:
        raise ValueError("Invalid client ID. Must be 1 or 2.")

    train_ratio = 0.8
    size = len(dataset)
    train_size = int(train_ratio * size)
    test_size = size - train_size

    generator = torch.Generator().manual_seed(42)
    train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size], generator=generator)

    batch_size = 32
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader


if __name__ == "__main__":
    trainloader1, testloader1 = load_data(1)
    trainloader2, testloader3 = load_data(2)

    print(testloader1)
