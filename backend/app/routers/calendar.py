from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/calendar",
    tags=["Public Calendar"]
)

@router.get("/events", response_model=List[schemas.CalendarEventResponse])
def get_public_calendar_events(db: Session = Depends(get_db)):
    
    # 2. Get today's date formatted exactly how your database stores it (YYYY-MM-DD)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 3. Add the date filter to your SQLAlchemy query
    approved_bookings = db.query(models.VenueBooking).filter(
        models.VenueBooking.status == "Approved",
        models.VenueBooking.date >= today_str # <-- Only fetch today and future dates
    ).all()

    public_events = []
    for booking in approved_bookings:
        # Retrieve the room name for the venue
        room = db.query(models.Room).filter(models.Room.id == booking.room_id).first()
        venue_name = room.name if room else "Venue TBA"

        public_events.append(
            schemas.CalendarEventResponse(
                id=booking.id,
                date=booking.date,
                time=booking.time,
                event_title=booking.event_title,
                event_type=booking.event_type,
                venue_name=venue_name
            )
        )
        
    return public_events

@router.get("/events/{event_id}", response_model=schemas.CalendarEventDetailResponse)
def get_event_details(event_id: int, db: Session = Depends(get_db)):
    # 1. Fetch the specific approved booking
    booking = db.query(models.VenueBooking).filter(
        models.VenueBooking.id == event_id,
        models.VenueBooking.status == "Approved"
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Event not found")

    # 2. Trace back to the Club to get the Organizer Name and Email
    organizer_name = "Student Club"
    contact_email = "Not provided"

    # Find the permission letter linked to this booking
    permission = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.generated_id == booking.permission_letter_id
    ).first()

    if permission:
        # Find the club using the user_id attached to the permission letter
        club = db.query(models.Club).filter(
            models.Club.user_id == permission.club_id
        ).first()
        
        if club:
            organizer_name = club.name
            if club.email:
                contact_email = club.email

    # 3. Return the mapped data
    return {
        "id": booking.id,
        "description": booking.description if booking.description else "No additional description provided.",
        "organizer": organizer_name,
        "contact_email": contact_email
    }

def approve_and_publish_event(booking_id: int, db: Session):
    # Finalizes the approval status of a venue booking and publishes it to the public calendar.
    booking = db.query(models.VenueBooking).filter(
        models.VenueBooking.id == booking_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Update the status to make it visible on the public calendar GET request
    booking.status = "Approved"
    db.commit()
    db.refresh(booking)
    
    return booking

