from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# We are using SQLite for local development. It will create a file named 'swifty.db'
SQLALCHEMY_DATABASE_URL = "sqlite:///./swifty.db"

# The engine is responsible for communicating with the database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Only needed for SQLite
)

# A SessionLocal instance is a workspace for your database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All our database models will inherit from this Base class
Base = declarative_base()