# database.py
# -----------------------------
# File này dùng để tạo: 
# - Engine kết nối MySQL
# - Session để thao tác DB
# -----------------------------

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Thay đổi theo thông tin MySQL của bạn
DB_USER = "root"
DB_PASS = "211005"
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "IE105"

# Format kết nối: mysql+pymysql://user:pass@host:port/db
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Tạo engine kết nối MySQL
engine = create_engine(DATABASE_URL)

# Tạo Session để CRUD database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo Base class để định nghĩa các bảng
Base = declarative_base()

# Dependency để FastAPI lấy session mỗi request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
