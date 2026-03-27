from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/calendar",
    tags=["Public Calendar"]
)

@router.get("/events", response_model=List[schemas.CalendarEventResponse])
def get_public_calendar_events(db: Session = Depends(get_db)):
    # Retrieves all approved upcoming events to be displayed on the public calendar.

    # Fetch bookings where the status is 'Approved' 
    approved_bookings = db.query(models.VenueBooking).filter(
        models.VenueBooking.status == "Approved"
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

