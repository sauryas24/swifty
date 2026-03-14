from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    
    # 1. Look for the user in the database by their email
    user = db.query(models.User).filter(models.User.email_id == credentials.email_id).first()
    
    # 2. If the user doesn't exist, or the password hash doesn't match, reject them
    if not user or not security.verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # 3. If the password matches generate temporary JWT token.
    # We hide the email and role inside the token.
    access_token = security.create_access_token(
        data={"sub": user.email_id, "role": user.role}
    )
    
    # 4. Send the token back to the frontend
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role,
        "username": user.username
    }