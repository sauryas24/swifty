from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas
from ..utils import security, email_service

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])

# We define the authority list so both endpoints can use it!
AUTHORITY_ROLES = ["admin", "authority", "gensec", "president", "facad", "adsa"]

# Endpoint 1: Create / Publish announcement
@router.post("/publish")
def publish_announcement(
    announcement_data: schemas.AnnouncementCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """Allows administrative authorities to publish announcements and emails targets."""

    # 1. Let ALL authority types publish
    if current_user.role not in AUTHORITY_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only administrative authorities can publish announcements."
        )

    # 2. Save the Announcement to the database
    target_string = ",".join(announcement_data.target_clubs) if announcement_data.target_clubs else ""
    
    new_announcement = models.Announcement(
        sender_id=current_user.id,
        heading=announcement_data.heading,
        message=announcement_data.message,
        target_clubs=target_string
    )

    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)

    # 3. Fetch the target users to get their email addresses
    if announcement_data.target_clubs:
        target_users = db.query(models.User).filter(
            models.User.username.in_(announcement_data.target_clubs),
            models.User.role == "coordinator"
        ).all()
    else:
        target_users = db.query(models.User).filter(models.User.role == "coordinator").all()

    # 4. Dispatch the emails!
    for user in target_users:
        email_service.send_notification_email(
            to_email=user.email_id,
            subject=f"New Announcement from {current_user.username}",
            body=f"Hello {user.username},\n\nYou have a new official announcement from {current_user.username}:\n\n{announcement_data.message}"
        )

    return {
        "id": new_announcement.id,
        "sender_username": current_user.username,
        "heading": new_announcement.heading, 
        "message": new_announcement.message,
        "target_clubs": announcement_data.target_clubs
    }

# Endpoint 2: View announcements
@router.get("/my-announcements")
def get_announcements(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Club coordinators can view announcements relevant to their club.
    Authorities can view ALL announcements on their dashboard.
    """
    announcements_with_senders = db.query(
        models.Announcement, 
        models.User.username.label("sender_username")
    ).join(
        models.User, models.Announcement.sender_id == models.User.id
    ).order_by(
        models.Announcement.id.desc()
    ).all()

    relevant_announcements = []

    for ann, sender_username in announcements_with_senders:
        if not ann.target_clubs:
            relevant_announcements.append({
                "id": ann.id,
                "sender_username": sender_username,
                "heading": ann.heading, 
                "message": ann.message,
                "target_clubs": [],
                "timestamp": ann.timestamp
            })
        else:
            clubs = ann.target_clubs.split(",")
            # Let Authorities see everything, but restrict Coordinators to their own!
            if current_user.role in AUTHORITY_ROLES or current_user.username in clubs:
                relevant_announcements.append({
                    "id": ann.id,
                    "sender_username": sender_username,
                    "heading": ann.heading, 
                    "message": ann.message,
                    "target_clubs": clubs,
                    "timestamp": ann.timestamp
                })

    return relevant_announcements