import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, schemas

from ..utils import email_service, security

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
    
    # Using positional arguments to prevent TypeError!
    email_sent = email_service.send_notification_email(
        request.email_id, 
        "Your Swifty Verification Code", 
        email_body
    )
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send the email. Please try again.")

    return {"message": f"OTP successfully sent to {request.email_id}"}



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
    
    # NOTE: If this is your login verify route, this is where your JWT generation 
    # (the "VIP wristband" code) SHOULD go, instead of in the approval route!
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

    # 2. Send the Authorization Email
    email_body = f"Hello {current_user.username},\n\nYou are attempting to approve a request on Swifty.\nYour authorization code is: {otp_code}\n\nThis code will expire in 5 minutes."
    

    email_sent = email_service.send_notification_email(
        current_user.email_id, 
        "Swifty Security: Approval Authorization Code", 
        email_body
    )
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send the email. Please try again.")


    return {"message": "Authorization OTP sent to your registered email."}

    

