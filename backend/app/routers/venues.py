from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from .. import models, schemas
from ..database import get_db

from ..utils.security import get_current_user 

router = APIRouter(
    prefix="/api/venues", 
    tags=["Venue Booking"]
)
def get_time_variants(time_str: str) -> List[str]:
    """Maps 12-hour frontend time strings to possible database formats (with and without spaces)."""
    mapping = {
        "09:00 AM - 11:00 AM": ["09:00 AM - 11:00 AM", "09:00 - 11:00", "09:00-11:00"],
        "11:00 AM - 01:00 PM": ["11:00 AM - 01:00 PM", "11:00 - 13:00", "11:00-13:00"],
        "02:00 PM - 04:00 PM": ["02:00 PM - 04:00 PM", "14:00 - 16:00", "14:00-16:00"],
        "04:00 PM - 06:00 PM": ["04:00 PM - 06:00 PM", "16:00 - 18:00", "16:00-18:00"],
        "06:00 PM - 08:00 PM": ["06:00 PM - 08:00 PM", "18:00 - 20:00", "18:00-20:00"]
    }
    return mapping.get(time_str, [time_str])

# GET AVAILABILITY (Public/Coordinator)
# Checks which rooms are open at a specific time. Requires no authentication so interfaces can query quickly.
@router.get("/availability", response_model=schemas.AvailabilityResponse)
def check_availability(
    date: str, 
    time: str, 
    db: Session = Depends(get_db)
):
    all_rooms = db.query(models.Room).all()
    
    # Locate all bookings that occur on the specified date and time, and are somewhere in the approval pipeline.
    time_variants = get_time_variants(time) # Get both formats
    
    conflicting_bookings = db.query(models.VenueBooking).filter(
        models.VenueBooking.date == date,
        models.VenueBooking.time.in_(time_variants), # <--- THE FIX
        models.VenueBooking.status.in_([
            "Pending GenSec", "Pending President", "Pending FacAd", "Pending ADSA", "Approved"
        ])
    ).all()
    
    # Identify exactly which rooms are taken to filter them out quickly.
    booked_room_ids = {booking.room_id for booking in conflicting_bookings} 
    
    available = []
    unavailable = []
    
    # Organize rooms into available and unavailable lists based on conflicts found above.
    for room in all_rooms:
        if room.id in booked_room_ids:
            unavailable.append(room)
        else:
            available.append(room)
    
    return {"available_rooms": available, "unavailable_rooms": unavailable}

# CREATE BOOKING (Protected Route)
# CREATE BOOKING (Protected Route)
# Logs a new venue booking request. Confirms the user is a coordinator, holds a valid approved permission, and double checks room availability.
@router.post("/book", status_code=status.HTTP_201_CREATED)
def submit_venue_booking(
    booking_data: schemas.BookingCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify the user is officially a coordinator before attempting any database modifications.
    if current_user.role != "coordinator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only Club Coordinators can book venues."
        )
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    if booking_data.date < today_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venue booking date cannot be in the past."
        )

    # Added with_for_update() to lock the room row 
    target_room = db.query(models.Room).filter(
        models.Room.id == booking_data.room_id
    ).with_for_update().first()
    
    if not target_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected room does not exist."
        )

    #Capacity Check 
    target_room = db.query(models.Room).filter(models.Room.id == booking_data.room_id).first()
    if not target_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected room does not exist."
        )
    
    if booking_data.expected_attendees > target_room.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected attendees ({booking_data.expected_attendees}) exceeds the capacity of {target_room.name} ({target_room.capacity})."
        )

    # Search for the permission letter referencing this specific generated ID.
    linked_permission = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.generated_id == booking_data.permission_letter_id
    ).first()

    if not linked_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Permission letter not found or invalid ID."
        )
        
    # Prevent a coordinator from hijacking a permission letter belonging to another club.
    if linked_permission.club_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You cannot book a venue using another club's permission letter."
        )
        
    # Ensure the permission letter successfully passed all administrative checks prior to this booking.
    if linked_permission.status != "Approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="This permission letter has not been fully approved yet."
        )

    # --- Prevent Permission Letter Reuse ---
    # Check if any active/approved venue booking already uses this ID.
    existing_booking = db.query(models.VenueBooking).filter(
        models.VenueBooking.permission_letter_id == booking_data.permission_letter_id,
        models.VenueBooking.status.in_([
            "Pending GenSec", "Pending President", "Pending FacAd", "Pending ADSA", "Approved"
        ])
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This permission letter ID has already been used for an active or approved venue booking."
        )

    # Perform a final check to guarantee no one secured the room in the time between searching and booking.
    time_variants = get_time_variants(booking_data.time) # Get both formats
    
    conflict = db.query(models.VenueBooking).filter(
        models.VenueBooking.date == booking_data.date,
        models.VenueBooking.time.in_(time_variants), 
        models.VenueBooking.room_id == booking_data.room_id,
        models.VenueBooking.status.in_([
            "Pending GenSec", "Pending President", "Pending FacAd", "Pending ADSA", "Approved"
        ])
    ).first()
    
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="The selected room has just been booked for the given date and time."
        )
    
    # Save the new venue request, placing it at the beginning of the administrative pipeline.
    new_booking = models.VenueBooking(
        date=booking_data.date,
        time=booking_data.time,
        room_id=booking_data.room_id,
        event_title=booking_data.event_title,
        event_type=booking_data.event_type,
        expected_attendees=booking_data.expected_attendees,
        description=booking_data.description,               
        permission_letter_id=booking_data.permission_letter_id,
        status="Pending GenSec" 
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    return {
        "message": "Booking request submitted successfully!", 
        "booking_id": new_booking.id,
        "status": new_booking.status
    }
