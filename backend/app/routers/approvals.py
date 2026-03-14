from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from .. import database, models, schemas
from ..utils import security, email_service
from .calendar import approve_and_publish_event

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])



# --- Shared Pipeline Configuration ---
# Since Venue and MoU use the exact same chain of command!
SHARED_PIPELINE = {
    "Pending GenSec": "Pending President",
    "Pending President": "Pending FacAd",
    "Pending FacAd": "Pending ADSA",
    "Pending ADSA": "Approved"
}

# Maps the current status to the user role required to approve it
ROLE_AUTHORIZATION_MAP = {
    "Pending GenSec": "gensec",
    "Pending President": "president",
    "Pending FacAd": "facad",
    "Pending ADSA": "adsa"
}

# ---------------------------------------------------------
# 1. VENUE BOOKING APPROVALS
# ---------------------------------------------------------
@router.put("/venue/{booking_id}/process")
def process_venue_approval(
    booking_id: int, 
    action_data: schemas.ApprovalAction, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Processes an approve/reject action for a Venue Booking."""
    booking = db.query(models.VenueBooking).filter(models.VenueBooking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Venue request not found")

    current_status = booking.status

    # Security Check
    required_role = ROLE_AUTHORIZATION_MAP.get(current_status)
    if current_user.role != required_role:
        raise HTTPException(status_code=403, detail=f"Not authorized. Current status requires role: {required_role}")

    # Handle Rejection
    if action_data.action == "reject":
        booking.status = f"Rejected by {current_user.role}"
        
        # ADD THIS LINE: Save the rejection message to the database
        booking.comments = action_data.message 
        
        db.commit()
        
        email_service.send_email(
            to="coordinator@institute.edu", 
            subject=f"Update: Request '{booking.event_title}' Rejected",
            body=f"Your venue request was rejected by {current_user.role}. Reason: {action_data.message}"
        )
        return {"message": "Venue request rejected successfully."}

    # Handle Approval
    elif action_data.action == "approve":
        if current_status not in SHARED_PIPELINE:
            raise HTTPException(status_code=400, detail="Request is already fully processed or rejected.")
            
        next_status = SHARED_PIPELINE[current_status]
        booking.status = next_status
        db.commit()
        
        # Final Approval 
        if next_status == "Approved":
            approve_and_publish_event(booking.id, db)
            
            email_service.send_email(
                to="coordinator@institute.edu",
                subject=f"Success! Request '{booking.event_title}' Approved",
                body="Your venue request has been fully approved and is now on the public calendar."
            )
            return {"message": "Final approval granted. Event published to calendar!"}
            
        # Intermediate Approval
        else:
            email_service.send_email(
                to="coordinator@institute.edu",
                subject=f"Progress: Request '{booking.event_title}' moved to {next_status}",
                body=f"Your venue request was approved by {current_user.role} and is now {next_status}."
            )
            return {"message": f"Request approved and moved to {next_status}."}
            
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")


# ---------------------------------------------------------
# 2. MoU PIPELINE APPROVALS
# ---------------------------------------------------------
@router.put("/mou/{mou_id}/process")
def process_mou_approval(
    mou_id: int, 
    action_data: schemas.ApprovalAction, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Processes an approve/reject action for an MoU Request."""
    mou = db.query(models.MoURequest).filter(models.MoURequest.id == mou_id).first()
    
    if not mou:
        raise HTTPException(status_code=404, detail="MoU request not found")

    current_status = mou.status

    # Security Check
    required_role = ROLE_AUTHORIZATION_MAP.get(current_status)
    if current_user.role != required_role:
        raise HTTPException(status_code=403, detail=f"Not authorized. Current status requires role: {required_role}")

    # Handle Rejection
    if action_data.action == "reject":
        mou.status = f"Rejected by {current_user.role}"
        if hasattr(mou, 'comments') and action_data.message:
            mou.comments = action_data.message
        db.commit()
        
        email_service.send_email(
            to="coordinator@institute.edu", 
            subject=f"Update: MoU Request '{mou.organization_name}' Rejected",
            body=f"Your MoU request was rejected by {current_user.role}. Reason: {action_data.message}"
        )
        return {"message": "MoU request rejected successfully."}

    # Handle Approval
    elif action_data.action == "approve":
        if current_status not in SHARED_PIPELINE:
            raise HTTPException(status_code=400, detail="Request is already fully processed or rejected.")
            
        next_status = SHARED_PIPELINE[current_status]
        mou.status = next_status
        db.commit()
        
        # Final Approval
        if next_status == "Approved":
            email_service.send_email(
                to="coordinator@institute.edu",
                subject=f"Success! MoU Request '{mou.organization_name}' Approved",
                body="Your MoU request has been fully approved."
            )
            return {"message": "Final approval granted for MoU!"}
            
        # Intermediate Approval
        else:
            email_service.send_email(
                to="coordinator@institute.edu",
                subject=f"Progress: MoU '{mou.organization_name}' moved to {next_status}",
                body=f"Your MoU request was approved by {current_user.role} and is now {next_status}."
            )
            return {"message": f"MoU approved and moved to {next_status}."}
            
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")