import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .. import database, models

# Security Settings (In a real app, hide the secret key in a .env file!)
SECRET_KEY = "swifty-super-secret-key-for-group-8"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120 # Token lasts for 2 hours

# Setup the password hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Creates the actual encrypted token string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

token_auth_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme), 
    db: Session = Depends(database.get_db)
):
    """
    This function intercepts requests, reads the token, and fetches the user.
    """
    
    # 1. Extract the raw token string
    token = credentials.credentials
    
    # 2. Define the error we will throw if the token is fake or expired
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 3. Try to decode the token using the secret key
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email_id: str = payload.get("sub")
        
        if email_id is None:
            raise credentials_exception
            
    except InvalidTokenError:
        # If the token is expired or tampered with, raise an error
        raise credentials_exception
        
    # 4. The token is valid! Find the user in the database
    user = db.query(models.User).filter(models.User.email_id == email_id).first()
    
    if user is None:
        raise credentials_exception
        
    # 5. Hand the verified user back to the router
    return user