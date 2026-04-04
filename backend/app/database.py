import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# 1. Force Python to find the .env file explicitly
# This gets the absolute path of the folder that database.py is sitting in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# If your .env is one folder OUTSIDE of your app folder, we go up one level
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env") 

load_dotenv(ENV_PATH)

# 2. Get the database URL 
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./swifty.db")

print(f"🔗 database.py is connecting to: {SQLALCHEMY_DATABASE_URL[:15]}...")

# SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)


# 3. Connect to the Database
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite requires special thread arguments
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Postgres does not need thread arguments
    # NEW
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Tests the connection before using it
        pool_recycle=300     # Automatically refreshes connections every 5 minutes
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()