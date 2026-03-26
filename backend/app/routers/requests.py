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
            "date": mou.created_at.strftime("%b %d, %Y") if mou.created_at else "N/A",
            "details": mou.organization_name,
            "purpose": mou.purpose, 
            "document_url": mou.document_url, 
            "status": simplify_status(mou.status),
            "raw_status": mou.status,
            "comments": mou.comments
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
            "comments": perm.comments,
            "generated_id": perm.generated_id
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

# Map the user's role to the exact status string they are allowed to approve
AUTHORITY_STATUS_MAP = {
    "gensec": "Pending GenSec",
    "president": "Pending President",
    "facad": "Pending FacAd",
    "adsa": "Pending ADSA",
    "dosa": "Pending DOSA"
}

@router.get("/pending")
def get_pending_requests_for_authority(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Fetches only the requests that are currently pending the logged-in authority's approval."""
    
    # 1. Security Check
    if current_user.role not in AUTHORITY_STATUS_MAP:
        raise HTTPException(status_code=403, detail="Not authorized to view the pending queue.")
        
    # 2. Figure out exactly what status this user is looking for
    target_status = AUTHORITY_STATUS_MAP[current_user.role]
    unified_records = []
    
    # 3. Fetch Pending MoUs
    mous = db.query(models.MoURequest).filter(models.MoURequest.status == target_status).all()
    for mou in mous:
        club = db.query(models.User).filter(models.User.id == mou.coordinator_id).first()
        unified_records.append({
            "id": mou.id,
            "club_name": club.username if club else "Unknown Club",
            "type": "MOU",
            "event_title": mou.organization_name,
            "expected_attendees": 0,
            "details": mou.purpose,
            "permission_letter_id": "N/A",
            "status": mou.status,
            "timestamp": mou.created_at.isoformat() if mou.created_at else "N/A"
        })
        
    # 4. Fetch Pending Permissions
    perms = db.query(models.PermissionLetter).filter(models.PermissionLetter.status == target_status).all()
    for perm in perms:
        club = db.query(models.User).filter(models.User.id == perm.club_id).first()
        unified_records.append({
            "id": perm.id,
            "club_name": club.username if club else "Unknown Club",
            "type": "PERMISSION",
            "event_title": perm.event_name,
            "expected_attendees": 0,
            "details": perm.reason,
            "permission_letter_id": "N/A",
            "status": perm.status,
            "timestamp": perm.date
        })
        
    # 5. Fetch Pending Venues
    venues = db.query(models.VenueBooking).filter(models.VenueBooking.status == target_status).all()
    for venue in venues:
        # Venue bookings don't store club_id directly, so we trace it back through the Permission Letter!
        club_name = "Unknown Club"
        perm = db.query(models.PermissionLetter).filter(models.PermissionLetter.generated_id == venue.permission_letter_id).first()
        if perm:
            club = db.query(models.User).filter(models.User.id == perm.club_id).first()
            if club:
                club_name = club.username

        unified_records.append({
            "id": venue.id,
            "club_name": club_name,
            "type": "VENUE",
            "event_title": venue.event_title,
            "expected_attendees": venue.expected_attendees,
            "details": venue.description,
            "permission_letter_id": venue.permission_letter_id,
            "status": venue.status,
            "timestamp": venue.date
        })
        
    return unified_records


@router.get("/club/{club_id}")
def get_club_requests_for_authority(
    club_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Fetches all requests (MoU, Permission, Venue) for a specific club's detailed view."""
    if current_user.role not in ["authority", "adsa", "dosa", "gensec", "president", "facad"]:
        raise HTTPException(status_code=403, detail="Not authorized.")

    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
        
    coordinator_id = club.user_id
    unified_records = []

    mous = db.query(models.MoURequest).filter(models.MoURequest.coordinator_id == coordinator_id).all()
    for mou in mous:
        unified_records.append({
            "id": mou.id,
            "type": "MOU",
            "event_title": mou.organization_name,
            "expected_attendees": 0,
            "details": mou.purpose,
            "status": simplify_status(mou.status),
            "timestamp": mou.created_at.strftime("%Y-%m-%d") if mou.created_at else ""
        })

    permissions = db.query(models.PermissionLetter).filter(models.PermissionLetter.club_id == coordinator_id).all()
    permission_gen_ids = [p.generated_id for p in permissions if p.generated_id]

    for perm in permissions:
        unified_records.append({
            "id": perm.id,
            "type": "PERMISSION",
            "event_title": perm.event_name,
            "expected_attendees": 0,
            "details": perm.reason,
            "status": simplify_status(perm.status),
            "timestamp": perm.date or ""
        })

    if permission_gen_ids:
        venues = db.query(models.VenueBooking).filter(
            models.VenueBooking.permission_letter_id.in_(permission_gen_ids)
        ).all()
        for venue in venues:
            unified_records.append({
                "id": venue.id,
                "type": "VENUE",
                "event_title": venue.event_title,
                "expected_attendees": venue.expected_attendees,
                "details": venue.description,
                "status": simplify_status(venue.status),
                "timestamp": venue.date or ""
            })

    unified_records.sort(key=lambda x: x["timestamp"], reverse=True)
    return unified_records