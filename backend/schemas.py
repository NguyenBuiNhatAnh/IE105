from pydantic import BaseModel

# Session
class TrainingSessionCreate(BaseModel):
    num_rounds: int
    lr: float
    local_epochs: int

class TrainingSessionOut(TrainingSessionCreate):
    id: int
    class Config:
        orm_mode = True

# Client submit
class ClientSubmitCreate(BaseModel):
    session_id: int
    client_id: int
    round_number: int
    accuracy: float
    seed: int

class ClientSubmitOut(ClientSubmitCreate):
    id: int
    timestamp: str
    class Config:
        orm_mode = True
