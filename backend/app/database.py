from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Creates a local file named swifty.db in your root folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./swifty.db"

# connect_args is needed only for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# THIS IS THE LINE PYTHON IS LOOKING FOR:
Base = declarative_base()

# This function provides a database session to your routers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()