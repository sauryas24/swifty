import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import email_service, security

router = APIRouter(prefix="/api/otp", tags=["OTP Verification"])

# 1. SEND OTP ENDPOINT
@router.post("/send")
def send_otp(request: schemas.OTPRequest, db: Session = Depends(database.get_db)):
    # Generate a random 6-digit code (e.g., "048291")
    otp_code = f"{random.randint(0, 999999):06d}"
    
    # Set expiration time to 5 minutes from now
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    # Check if this email already has an OTP in the database
    existing_otp = db.query(models.OTP).filter(models.OTP.email_id == request.email_id).first()
    
    if existing_otp:
        # Update the existing record so we don't clutter the database
        existing_otp.otp_code = otp_code
        existing_otp.expires_at = expiration_time.isoformat()
    else:
        # Create a new record
        new_otp = models.OTP(
            email_id=request.email_id,
            otp_code=otp_code,
            expires_at=expiration_time.isoformat()
        )
        db.add(new_otp)
        
    db.commit()

    # Dispatch the email!
    email_body = f"""
    Hello,
    
    Your verification code for Swifty is: {otp_code}
    
    This code will expire in 5 minutes. Please do not share this code with anyone.
    """
    
    email_sent = email_service.send_notification_email(
        to_email=request.email_id,
        subject="Your Swifty Verification Code",
        body=email_body
    )
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send the email. Please try again.")

    return {"message": f"OTP successfully sent to {request.email_id}"}


# 2. VERIFY OTP ENDPOINT
# 2. VERIFY OTP ENDPOINT
@router.post("/verify")
def verify_otp(request: schemas.OTPVerify, db: Session = Depends(database.get_db)):
    # Find the OTP record for this email
    otp_record = db.query(models.OTP).filter(models.OTP.email_id == request.email_id).first()
    
    if not otp_record:
        raise HTTPException(status_code=404, detail="No OTP requested for this email.")
        
    # Check if the code matches
    if otp_record.otp_code != request.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")
        
    # Check if the code is expired
    current_time = datetime.now(timezone.utc)
    expiration_time = datetime.fromisoformat(otp_record.expires_at)
    
    if current_time > expiration_time:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        
    # If we pass all checks, the OTP is valid! 
    # Delete it from the database so it cannot be used again.
    db.delete(otp_record)
    db.commit()
    
    # ---------------------------------------------------------
    # NEW CODE: Fetch the User and hand over the VIP wristband!
    # ---------------------------------------------------------
    
    # 1. Find the actual user in the database
    user = db.query(models.User).filter(models.User.email_id == request.email_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found in the system.")

    # 2. GENERATE THE TOKEN 
    # IMPORTANT: You must import your token function at the top of this file!
    # If your token function is in a file called oauth2.py, it looks like this:
    from ..utils.security import create_access_token # <-- UPDATE THIS IMPORT IF NEEDED
    
    # Create the token (ensure the data matches what your app normally expects)
    access_token = create_access_token(data={"user_id": user.id}) 

    # 3. Send the full package back to the frontend!
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "club_id": getattr(user, 'club_id', None), # Safely get club_id if it exists
        "message": "Email successfully verified!"
    }