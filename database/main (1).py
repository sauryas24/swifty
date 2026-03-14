from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import SessionLocal, engine

# Ensure tables are created (a good fallback)
models.Base.metadata.create_all(bind=engine)

# Initialize the FastAPI app
app = FastAPI(title="Swifty Gymkhana API")

# --- DATABASE DEPENDENCY ---
# This opens a connection to the database for a single request, then safely closes it
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API ROUTES ---

# 1. A simple health check route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Swifty Backend!"}

# 2. Route to create a new user
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    
    # Check if the email is already registered
    existing_user = db.query(models.User).filter(models.User.iitk_email == user.iitk_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create the new user object based on our models.py blueprint
    db_user = models.User(
        name=user.name,
        iitk_email=user.iitk_email,
        password_hash=user.password_hash,
        role=user.role
    )
    
    # Add to the database and save (commit)
    db.add(db_user)
    db.commit()
    
    # Refresh retrieves the newly generated ID from the database
    db.refresh(db_user)
    
    return db_user