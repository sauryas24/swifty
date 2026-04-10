import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, schemas

from ..utils import email_service, security

router = APIRouter(prefix="/api/otp", tags=["OTP Verification"])

#  LOGIN / REGISTRATION (Unauthenticated)
# Generates and emails a 6-digit code for users trying to log in.
@router.post("/send")
def send_otp(request: schemas.OTPRequest, db: Session = Depends(database.get_db)):
    
    # Validate that the email exists in the users table to prevent abuse and database bloat
    user = db.query(models.User).filter(models.User.email_id == request.email_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid request. Email not registered.")

    # Generate a random 6-digit number and set it to expire in 5 minutes.
    otp_code = f"{random.randint(0, 999999):06d}"
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    # Check if this email already requested an OTP recently. If yes, update it; otherwise, create a new entry.
    existing_otp = db.query(models.OTP).filter(models.OTP.email_id == request.email_id).first()
    if existing_otp:
        existing_otp.otp_code = otp_code
        existing_otp.expires_at = expiration_time.isoformat()
    else:
        new_otp = models.OTP(email_id=request.email_id, otp_code=otp_code, expires_at=expiration_time.isoformat())
        db.add(new_otp)
        
    db.commit()

    # Dispatch the code to the user via email.
    email_body = f"Hello,\n\nYour verification code for Swifty is: {otp_code}\n\nThis code will expire in 5 minutes."
    
    email_sent = email_service.send_notification_email(
        request.email_id, 
        "Your Swifty Verification Code", 
        email_body
    )
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send the email. Please try again.")

    return {"message": f"OTP successfully sent to {request.email_id}"}


# Confirms the user entered the correct code during the login process.
@router.post("/verify")
def verify_otp(request: schemas.OTPVerify, db: Session = Depends(database.get_db)):
    
    # Locate the saved OTP record matching the email.
    otp_record = db.query(models.OTP).filter(models.OTP.email_id == request.email_id).first()
    if not otp_record:
        raise HTTPException(status_code=404, detail="No OTP requested for this email.")
        
    # Check if the code they entered matches our records.
    if otp_record.otp_code != request.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")
        
    # Check if the 5-minute time window has passed.
    current_time = datetime.now(timezone.utc)
    expiration_time = datetime.fromisoformat(otp_record.expires_at)
    
    if current_time > expiration_time:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        
    # Clean up the database once the code is successfully used.
    db.delete(otp_record)
    db.commit()
    
    return {"message": "Email successfully verified!"}


#  APPROVALS (Authenticated & Secure)
# Employs a secondary OTP check to secure sensitive administrative decisions (like approving an event).
@router.post("/send-approval")
def send_approval_otp(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user) 
):
    # Create a fresh 6-digit code with a 5-minute lifespan.
    otp_code = f"{random.randint(0, 999999):06d}"
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    # Store the OTP in the database linked directly to the authenticated user's email.
    existing_otp = db.query(models.OTP).filter(models.OTP.email_id == current_user.email_id).first()
    
    if existing_otp:
        existing_otp.otp_code = otp_code
        existing_otp.expires_at = expiration_time.isoformat()
    else:
        new_otp = models.OTP(
            email_id=current_user.email_id, 
            otp_code=otp_code, 
            expires_at=expiration_time.isoformat()
        )
        db.add(new_otp)
        
    db.commit()

    # Send the authorization email detailing the action they are attempting to perform.
    email_body = f"Hello {current_user.username},\n\nYou are attempting to approve a request on Swifty.\nYour authorization code is: {otp_code}\n\nThis code will expire in 5 minutes."
    
    email_sent = email_service.send_notification_email(
        current_user.email_id, 
        "Swifty Security: Approval Authorization Code", 
        email_body
    )
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send the email. Please try again.")

    return {"message": "Authorization OTP sent to your registered email."}