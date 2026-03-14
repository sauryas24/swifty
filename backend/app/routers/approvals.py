from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

# Adjust these imports based on your actual file structure
from .. import database, models
from ..utils import security, email_service
from .calendar import approve_and_publish_event

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

# --- Schemas ---
class ApprovalAction(BaseModel):
    action: str  # Must be "approve" or "reject"
    message: Optional[str] = None  # Optional reason for rejection

# --- Pipeline Configuration ---
# This dictionary defines what the next status is after a successful approval
APPROVAL_PIPELINE = {
    "Pending GenSec": "Pending President",
    "Pending President": "Pending FacAd",
    "Pending FacAd": "Pending ADSA",
    "Pending ADSA": "Approved"
}

# --- Endpoints ---
@router.put("/{booking_id}/process")
def process_approval(
    booking_id: int, 
    action_data: ApprovalAction, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Processes an approve/reject action from an authority figure in the pipeline.
    """
    # 1. Fetch the booking
    booking = db.query(models.VenueBooking).filter(models.VenueBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Request not found")

    current_status = booking.status
    
    # Optional: You can add security checks here to ensure the current_user.role 
    # matches the current_status (e.g., if status is "Pending GenSec", user role must be "gensec")

    # 2. Handle Rejection
    if action_data.action == "reject":
        booking.status = f"Rejected by {current_user.role}"
        # Assuming you added a rejection_reason column to your model
        # booking.rejection_reason = action_data.message 
        
        db.commit()
        
        # Send rejection email to coordinator
        email_service.send_email(
            to="coordinator@institute.edu", # In reality, fetch from booking.user.email
            subject=f"Update: Request '{booking.event_title}' Rejected",
            body=f"Your request was rejected by {current_user.role}. Reason: {action_data.message}"
        )
        return {"message": "Request rejected successfully."}

    # 3. Handle Approval
    elif action_data.action == "approve":
        if current_status not in APPROVAL_PIPELINE:
            raise HTTPException(status_code=400, detail="Request is already fully processed or rejected.")
            
        next_status = APPROVAL_PIPELINE[current_status]
        booking.status = next_status
        db.commit()
        
        # 4. Handle Final Approval (ADSA)
        if next_status == "Approved":
            # Call the function we wrote earlier to publish it!
            approve_and_publish_event(booking.id, db)
            
            email_service.send_email(
                to="coordinator@institute.edu",
                subject=f"Success! Request '{booking.event_title}' Approved",
                body="Your request has been fully approved by the ADSA and is now on the public calendar."
            )
            return {"message": "Final approval granted. Event published to calendar!"}
            
        # 5. Handle Intermediate Approval (Move to next authority)
        else:
            # Notify coordinator of progress
            email_service.send_email(
                to="coordinator@institute.edu",
                subject=f"Progress: Request '{booking.event_title}' moved to {next_status}",
                body=f"Your request was approved by {current_user.role} and is now {next_status}."
            )
            
            # Notify the NEXT authority in the chain
            email_service.send_email(
                to=f"next_authority@institute.edu", # You'd dynamically fetch the right email here
                subject=f"Action Required: New Request Pending Approval",
                body=f"A new request '{booking.event_title}' requires your approval."
            )
            
            return {"message": f"Request approved and moved to {next_status}."}
            
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")