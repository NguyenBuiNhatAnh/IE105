from sqlalchemy.orm import Session
import models, schemas

# --------- Session ---------
def create_session(db: Session, session: schemas.TrainingSessionCreate):
    db_item = models.TrainingSession(**session.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_sessions(db: Session):
    return db.query(models.TrainingSession).all()


# --------- ClientSubmit ---------
def create_submit(db: Session, submit: schemas.ClientSubmitCreate):
    """
    Lưu dữ liệu submit của client vào DB
    """
    db_item = models.ClientSubmit(**submit.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_submits_by_client(db: Session, client_id: int, session_id: int = None):
    """
    Lấy tất cả submit của client_id, có thể lọc theo session_id
    """
    query = db.query(models.ClientSubmit).filter(models.ClientSubmit.client_id == client_id)
    if session_id:
        query = query.filter(models.ClientSubmit.session_id == session_id)
    return query.order_by(models.ClientSubmit.round_number).all()
