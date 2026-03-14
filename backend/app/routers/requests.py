from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/requests", tags=["Request Records"])

def simplify_status(raw_status: str) -> str:
    """Helper function to convert backend statuses to UI badges."""
    status_lower = raw_status.lower() if raw_status else ""
    if "approved" in status_lower:
        return "Approved"
    elif "reject" in status_lower: # Catches "Rejected by facad", etc.
        return "Rejected"
    else:
        return "Pending"

@router.get("/all", response_model=List[schemas.RequestRecordResponse])
def get_all_user_requests(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Fetches all MoUs, Permissions, and Venues for the logged-in coordinator.
    """
    if current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Only coordinators can view this dashboard.")

    unified_records = []

    # 1. Fetch MoU Requests
    mous = db.query(models.MoURequest).filter(models.MoURequest.coordinator_id == current_user.id).all()
    for mou in mous:
        unified_records.append({
            "id": mou.id,
            "type": "MOU",
            # Fallback to "N/A" if you don't have a date column yet
            "date": getattr(mou, 'date', "N/A"), 
            "details": mou.organization_name,
            "status": simplify_status(mou.status),
            "raw_status": mou.status,
            "comments": mou.comments # This now perfectly pulls the rejection reason!
        })

    # 2. Fetch Permission Letters
    permissions = db.query(models.PermissionLetter).filter(models.PermissionLetter.club_id == current_user.id).all()
    permission_ids = [str(p.id) for p in permissions]

    for perm in permissions:
        unified_records.append({
            "id": perm.id,
            "type": "PERMISSION",
            "date": getattr(perm, 'date', "N/A"),
            "details": perm.event_name,
            "status": simplify_status(perm.status),
            "raw_status": perm.status,
            "comments": perm.comments
        })

    # 3. Fetch Venue Bookings 
    if permission_ids:
        venues = db.query(models.VenueBooking).filter(
            models.VenueBooking.permission_letter_id.in_(permission_ids)
        ).all()
        
        for venue in venues:
            unified_records.append({
                "id": venue.id,
                "type": "VENUE",
                "date": venue.date, 
                "details": venue.event_title,
                "status": simplify_status(venue.status),
                "raw_status": venue.status,
                "comments": venue.comments
            })

    # 4. Sort the combined list by date (newest first)
    unified_records.sort(key=lambda x: x["date"], reverse=True)

    return unified_records