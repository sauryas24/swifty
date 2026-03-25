import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import email_service, security
from ..utils import email_service, security # Added security import!

router = APIRouter(prefix="/api/otp", tags=["OTP Verification"])

# ==========================================
# 1. LOGIN / REGISTRATION (Unauthenticated)
# ==========================================
@router.post("/send")
def send_otp(request: schemas.OTPRequest, db: Session = Depends(database.get_db)):
    otp_code = f"{random.randint(0, 999999):06d}"
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    existing_otp = db.query(models.OTP).filter(models.OTP.email_id == request.email_id).first()
    if existing_otp:
        existing_otp.otp_code = otp_code
        existing_otp.expires_at = expiration_time.isoformat()
    else:
        new_otp = models.OTP(email_id=request.email_id, otp_code=otp_code, expires_at=expiration_time.isoformat())
        db.add(new_otp)
        
    db.commit()

    email_body = f"Hello,\n\nYour verification code for Swifty is: {otp_code}\n\nThis code will expire in 5 minutes."
    email_sent = email_service.send_notification_email(to_email=request.email_id, subject="Your Swifty Verification Code", body=email_body)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send the email. Please try again.")

    return {"message": f"OTP successfully sent to {request.email_id}"}


# 2. VERIFY OTP ENDPOINT
# 2. VERIFY OTP ENDPOINT
@router.post("/verify")
def verify_otp(request: schemas.OTPVerify, db: Session = Depends(database.get_db)):
    """Used ONLY for Login/Registration."""
    otp_record = db.query(models.OTP).filter(models.OTP.email_id == request.email_id).first()
    if not otp_record:
        raise HTTPException(status_code=404, detail="No OTP requested for this email.")
        
    if otp_record.otp_code != request.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")
        
    current_time = datetime.now(timezone.utc)
    expiration_time = datetime.fromisoformat(otp_record.expires_at)
    
    if current_time > expiration_time:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        
    db.delete(otp_record)
    db.commit()
    return {"message": "Email successfully verified!"}


# ==========================================
# 2. APPROVALS (Authenticated & Secure)
# ==========================================
@router.post("/send-approval")
def send_approval_otp(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user) # Extracts user from JWT!
):
    """
    Used when an authority clicks 'Approve' on a dashboard.
    It automatically sends the OTP to their registered email address.
    """
    otp_code = f"{random.randint(0, 999999):06d}"
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    
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
    existing_otp = db.query(models.OTP).filter(models.OTP.email_id == current_user.email_id).first()
    
    if existing_otp:
        existing_otp.otp_code = otp_code
        existing_otp.expires_at = expiration_time.isoformat()
    else:
        new_otp = models.OTP(email_id=current_user.email_id, otp_code=otp_code, expires_at=expiration_time.isoformat())
        db.add(new_otp)
        
    db.commit()

    email_body = f"Hello {current_user.username},\n\nYou are attempting to approve a request on Swifty.\nYour authorization code is: {otp_code}\n\nThis code will expire in 5 minutes."
    email_sent = email_service.send_notification_email(
        current_user.email_id, 
        "Swifty Security: Approval Authorization Code", 
        email_body
    )
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send the email. Please try again.")

    return {"message": "Authorization OTP sent to your registered email."}
