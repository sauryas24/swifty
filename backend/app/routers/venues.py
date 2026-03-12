from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/venues", tags=["Venue Booking"])

#Endpoint 1: Check availability of rooms given a date and time
@router.get("/availability", response_model=schemas.AvailabilityResponse)
def check_availability(date: str, time: str, db: Session = Depends(database.get_db)):
    """
    Frontend sends the date and time for which the backend responds with a list of available and unavailable rooms.
    """
    # Get all the rooms
    all_rooms = db.query(models.Room).all()
    
    # Find all the bookings that overlap with given date and time
    conflicting_bookings = db.query(models.VenueBooking).filter(
        models.VenueBooking.date == date,
        models.VenueBooking.time == time
    ).all()
    
    # Extract the room IDs from the overlaps
    booked_room_ids = [booking.room_id for booking in conflicting_bookings]
    
    # Separate available and unavailable rooms
    available = []
    unavailable = []
    
    for room in all_rooms:
        if room.id in booked_room_ids:
            unavailable.append(room)
        else:
            available.append(room)
    
    return {"available_rooms": available, "unavailable_rooms": unavailable}

# Endpoint 2: Submit a booking request
@router.post("/book")
def submit_venue_booking(
    booking_data: schemas.BookingCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)):
    """
    Receives the booking details from the frontend and creates a new booking entry in the database with status as pending.
    """
    
    # Only authenticated users can book a venue, so we use the get_current_user dependency to ensure the user is logged in.
    if current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Only Club Coordinators can book venues.")
    
    # Check to ensure the room wasn't booked
    conflict = db.query(models.VenueBooking).filter(
        models.VenueBooking.date == booking_data.date,
        models.VenueBooking.time == booking_data.time,
        models.VenueBooking.room_id == booking_data.room_id
    ).first()
    
    if conflict:
        raise HTTPException(status_code=400, detail="The selected room is already booked for the given date and time.")
    
    new_booking = models.VenueBooking(
        date=booking_data.date,
        time=booking_data.time,
        room_id=booking_data.room_id,
        event_title=booking_data.event_title,
        event_type=booking_data.event_type,
        expected_attendees=booking_data.expected_attendees,
        description=booking_data.description,
        permission_letter_id=booking_data.permission_letter_id
    )
    
    # Add the new booking to the database
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    return {"message": "Booking request submitted successfully!", "booking_id": new_booking.id}