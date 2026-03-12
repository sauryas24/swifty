from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])


# Endpoint 1: Create / Publish announcement
@router.post("/publish", response_model=schemas.AnnouncementResponse)
def publish_announcement(
    announcement_data: schemas.AnnouncementCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Allows administrative authorities to publish announcements.
    """

    # Only authorities allowed
    if current_user.role not in ["admin", "authority"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrative authorities can publish announcements."
        )

    new_announcement = models.Announcement(
        sender_id=current_user.id,
        message=announcement_data.message,
        target_clubs=",".join(announcement_data.target_clubs)
    )

    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)

    return new_announcement


# Endpoint 2: View announcements for a club coordinator
@router.get("/my-announcements", response_model=List[schemas.AnnouncementResponse])
def get_announcements(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Club coordinators can view announcements relevant to their club.
    """

    if current_user.role != "coordinator":
        raise HTTPException(
            status_code=403,
            detail="Only club coordinators can view announcements."
        )

    announcements = db.query(models.Announcement).all()

    relevant_announcements = []

    for announcement in announcements:
        if announcement.target_clubs is None:
            relevant_announcements.append(announcement)
        else:
            clubs = announcement.target_clubs.split(",")
            if current_user.club_name in clubs:
                relevant_announcements.append(announcement)

    return relevant_announcements