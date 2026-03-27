from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import security
from .otp import send_otp, verify_otp

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Verifying Password & Dispatching OTP
@router.post("/login")
def login_step_1(credentials: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    
    # Look for the user and verify their password
    user = db.query(models.User).filter(models.User.email_id == credentials.email_id).first()

    if not user or not security.verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # If password is correct, we  call the otp.py function
    # This automatically generates the code, saves it to SQLite, and sends the IITK email.
    otp_request_data = schemas.OTPRequest(email_id=user.email_id)
    send_otp(otp_request_data, db)  
    
    return {
        "message": "Password verified. OTP sent to your email.",
        "requires_2fa": True,
        "email_id": user.email_id
    }


# Verify OTP & Issue JWT
@router.post("/login/verify", response_model=schemas.Token)
def login_step_2(request: schemas.OTPVerify, db: Session = Depends(database.get_db)):
    
    # Call the otp.py function to verify the 6-digit code.
    # If the code is wrong or expired, the otp.py file will automatically throw the HTTPException!
    verify_otp(request, db)
    
    # If the code succeeds without throwing an error, we are issue the JWT.
    user = db.query(models.User).filter(models.User.email_id == request.email_id).first()
    
    access_token = security.create_access_token(
        data={"sub": user.email_id, "role": user.role}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "id" : user.id,
    }