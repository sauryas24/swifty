from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from .. import database, models, schemas
from ..utils import security, email_service
from .calendar import approve_and_publish_event

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

# Configuration for the sequential approval workflow
SHARED_PIPELINE = {
    "Pending GenSec": "Pending President",
    "Pending President": "Pending FacAd",
    "Pending FacAd": "Pending ADSA",
    "Pending ADSA": "Approved"
}

ROLE_AUTHORIZATION_MAP = {
    "Pending GenSec": "gensec",
    "Pending President": "president",
    "Pending FacAd": "facad",
    "Pending ADSA": "adsa"
}


# OTP Verification
def _verify_otp(email_id: str, otp_code: str, db: Session):
    """Validates the OTP, checks expiration, and consumes it."""
    if not otp_code:
        raise HTTPException(status_code=400, detail="An OTP code is required to approve this request.")
        
    otp_record = db.query(models.OTP).filter(models.OTP.email_id == email_id).first()
    
    if not otp_record or otp_record.otp_code != otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")
        
    # Check if expired (Comparing ISO strings)
    current_time = datetime.now(timezone.utc).isoformat()
    if current_time > otp_record.expires_at:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        
    #  If Valid, delete it so it cannot be used twice
    db.delete(otp_record)
    db.commit()


# VENUE BOOKING APPROVALS
@router.put("/venue/{booking_id}/process")
def process_venue_approval(
    booking_id: int, 
    action_data: schemas.ApprovalAction, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Processes approval or rejection for venue booking requests.
    booking = db.query(models.VenueBooking).filter(models.VenueBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Venue request not found")

    current_status = booking.status
    required_role = ROLE_AUTHORIZATION_MAP.get(current_status)
    if current_user.role != required_role:
        raise HTTPException(status_code=403, detail=f"Not authorized. Current status requires role: {required_role}")

    # --- DYNAMIC EMAIL LOOKUP ---
    target_email = "goyalvasu63@gmail.com" # Safe fallback
    linked_permission = db.query(models.PermissionLetter).filter(models.PermissionLetter.generated_id == booking.permission_letter_id).first()
    if linked_permission:
        club = db.query(models.Club).filter(models.Club.user_id == linked_permission.club_id).first()
        if club and club.email:
            target_email = club.email
    # ----------------------------

    if action_data.action == "reject":
        booking.status = f"Rejected by {current_user.role}"
        booking.comments = action_data.message 
        db.commit()
        
        email_service.send_notification_email(
            target_email, 
            f"Update: Request '{booking.event_title}' Rejected",
            f"Your venue request was rejected by {current_user.role}. Reason: {action_data.message}"
        )
        return {"message": "Venue request rejected successfully."}

    elif action_data.action == "approve":
        if current_status not in SHARED_PIPELINE:
            raise HTTPException(status_code=400, detail="Request is already fully processed or rejected.")
            
        # OTP security check
        _verify_otp(current_user.email_id, action_data.otp_code, db)
            
        next_status = SHARED_PIPELINE[current_status]
        booking.status = next_status
        db.commit()
        
        if next_status == "Approved":
            approve_and_publish_event(booking.id, db)
            email_service.send_notification_email(
                target_email,
                f"Success! Request '{booking.event_title}' Approved",
                "Your venue request has been fully approved and is now on the public calendar."
            )
            return {"message": "Final approval granted. Event published to calendar!"}
        else:
            email_service.send_notification_email(
                target_email,
                f"Progress: Request '{booking.event_title}' moved to {next_status}",
                f"Your venue request was approved by {current_user.role} and is now {next_status}."
            )
            return {"message": f"Request approved and moved to {next_status}."}
            
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")


# MoU PIPELINE APPROVALS
@router.put("/mou/{mou_id}/process")
def process_mou_approval(
    mou_id: int, 
    action_data: schemas.ApprovalAction, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Processes approval or rejection for MoU requests."""
    mou = db.query(models.MoURequest).filter(models.MoURequest.id == mou_id).first()
    if not mou:
        raise HTTPException(status_code=404, detail="MoU request not found")

    current_status = mou.status
    required_role = ROLE_AUTHORIZATION_MAP.get(current_status)
    if current_user.role != required_role:
        raise HTTPException(status_code=403, detail=f"Not authorized. Current status requires role: {required_role}")

    # --- DYNAMIC EMAIL LOOKUP ---
    target_email = "goyalvasu63@gmail.com" # Safe fallback
    club = db.query(models.Club).filter(models.Club.user_id == mou.coordinator_id).first()
    if club and club.email:
        target_email = club.email
    # ----------------------------

    if action_data.action == "reject":
        mou.status = f"Rejected by {current_user.role}"
        if hasattr(mou, 'comments') and action_data.message:
            mou.comments = action_data.message
        db.commit()
        
        email_service.send_notification_email(
            target_email, 
            f"Update: MoU Request '{mou.organization_name}' Rejected",
            f"Your MoU request was rejected by {current_user.role}. Reason: {action_data.message}"
        )
        return {"message": "MoU request rejected successfully."}

    elif action_data.action == "approve":
        if current_status not in SHARED_PIPELINE:
            raise HTTPException(status_code=400, detail="Request is already fully processed or rejected.")
            
        # OTP security check
        _verify_otp(current_user.email_id, action_data.otp_code, db)
            
        next_status = SHARED_PIPELINE[current_status]
        mou.status = next_status
        db.commit()
        
        if next_status == "Approved":
            email_service.send_notification_email(
                target_email,
                f"Success! MoU Request '{mou.organization_name}' Approved",
                "Your MoU request has been fully approved."
            )
            return {"message": "Final approval granted for MoU!"}
        else:
            email_service.send_notification_email(
                target_email,
                f"Progress: MoU '{mou.organization_name}' moved to {next_status}",
                f"Your MoU request was approved by {current_user.role} and is now {next_status}."
            )
            return {"message": f"MoU approved and moved to {next_status}."}
            
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")


# PERMISSION LETTER APPROVALS
def _generate_permission_letter_id(db: Session) -> str:
    # Generates a sequential ID for finalized permission letters.
    year = datetime.now().year
    prefix = f"PL-{year}-"
    approved_this_year = db.query(models.PermissionLetter).filter(models.PermissionLetter.generated_id.like(f"{prefix}%")).count()
    sequence = approved_this_year + 1
    return f"{prefix}{sequence:04d}" 

@router.put("/permission/{letter_id}/process")
def process_permission_approval(
    letter_id: int,
    action_data: schemas.ApprovalAction,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    letter = db.query(models.PermissionLetter).filter(models.PermissionLetter.id == letter_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail="Permission letter not found")

    current_status = letter.status
    required_role = ROLE_AUTHORIZATION_MAP.get(current_status)
    
    if not required_role:
        raise HTTPException(status_code=400, detail="This request is already fully processed or rejected.")
    if current_user.role != required_role:
        raise HTTPException(status_code=403, detail=f"Not authorized. Current status requires role: {required_role}")

    # --- DYNAMIC EMAIL LOOKUP ---
    club = db.query(models.Club).filter(models.Club.user_id == letter.club_id).first()
    target_email = club.email if club and club.email else "goyalvasu63@gmail.com"
    target_name = club.name if club else "Coordinator"
    # ----------------------------

    if action_data.action == "reject":
        letter.status = f"Rejected by {current_user.role}"
        letter.comments = action_data.message
        db.commit()

        email_service.send_notification_email(
            target_email, 
            f"Update: Permission Letter '{letter.event_name}' Rejected",
            (
                f"Hello {target_name},\n\n"
                f"Your permission letter for '{letter.event_name}' was rejected "
                f"by {current_user.role}. Reason: {action_data.message}"
            )
        )
        return {"message": "Permission letter rejected successfully."}

    elif action_data.action == "approve":
        if current_status not in SHARED_PIPELINE:
            raise HTTPException(status_code=400, detail="Request is already fully processed or rejected.")

        # OTP security check
        _verify_otp(current_user.email_id, action_data.otp_code, db)

        next_status = SHARED_PIPELINE[current_status]
        letter.status = next_status
        

        if next_status == "Approved":
            generated_id = _generate_permission_letter_id(db)
            letter.generated_id = generated_id
            db.commit()

            email_service.send_notification_email(
                target_email, 
                f"Permission Letter '{letter.event_name}' Approved",
                (
                    f"Hello {target_name},\n\n"
                    f"Your permission letter for '{letter.event_name}' has been fully approved!\n\n"
                    f"Your Official Permission Letter ID is: {generated_id}\n\n"
                    f"Please use this ID when submitting a Venue Booking request."
                )
            )
            return {
                "message": "Final approval granted. Permission Letter ID generated.",
                "generated_id": generated_id
            }
        else:
            db.commit()
            email_service.send_notification_email(
                target_email, 
                f"Progress: Permission Letter '{letter.event_name}' moved to {next_status}",
                f"Hello {target_name},\n\nYour permission letter was approved by {current_user.role} and is now {next_status}."
            )
            return {"message": f"Permission letter approved and moved to {next_status}."}

    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")
    
# Look up a Permission Letter by its generated ID
@router.get("/permission/lookup/{generated_id}", response_model=schemas.PermissionLetterResponse)
def lookup_permission_letter(
    generated_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Retrieves an approved permission letter using its designated ID.
    letter = db.query(models.PermissionLetter).filter(models.PermissionLetter.generated_id == generated_id).first()
    if not letter:
        raise HTTPException(status_code=404, detail=f"No approved permission letter found with ID '{generated_id}'.")
    return letter