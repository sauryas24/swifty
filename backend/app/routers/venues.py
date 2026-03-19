from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Import your local modules
from .. import models, schemas
from ..database import get_db

# Assuming you have a dependency that extracts the user from the JWT token
from ..utils.security import get_current_user 

router = APIRouter(
    prefix="/api/venues", 
    tags=["Venue Booking"]
)

# ==========================================
# 1. GET AVAILABILITY (Public/Coordinator)
# ==========================================
@router.get("/availability", response_model=schemas.AvailabilityResponse)
def check_availability(
    date: str, 
    time: str, 
    db: Session = Depends(get_db)
):
    """
    Checks which rooms are available for a given date and time slot.
    This does not require authentication so the frontend can query it instantly.
    """
    all_rooms = db.query(models.Room).all()
    
    # Find all the bookings that overlap with given date and time 
    conflicting_bookings = db.query(models.VenueBooking).filter(
        models.VenueBooking.date == date,
        models.VenueBooking.time == time,
        # UPDATE: Include the new pipeline steps to prevent double-booking!
        models.VenueBooking.status.in_([
            "Pending GenSec", 
            "Pending President", 
            "Pending FacAd", 
            "Pending ADSA", 
            "Approved"
        ])
    ).all()
    
    # Extract the room IDs from the overlaps
    booked_room_ids = {booking.room_id for booking in conflicting_bookings} # Set for O(1) lookup
    
    available = []
    unavailable = []
    
    for room in all_rooms:
        if room.id in booked_room_ids:
            unavailable.append(room)
        else:
            available.append(room)
    
    return {"available_rooms": available, "unavailable_rooms": unavailable}

# ==========================================
# 2. CREATE BOOKING (Protected Route)
# ==========================================
@router.post("/book", status_code=status.HTTP_201_CREATED)
def submit_venue_booking(
    booking_data: schemas.BookingCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Creates a new venue booking. Enforces Role-Based Access Control (RBAC) 
    and validates that the permission letter belongs to the user.
    """
    
    # --- 1. Role Authorization Check ---
    if current_user.role != "coordinator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only Club Coordinators can book venues."
        )

    # --- 2. Permission Letter Validation (CRITICAL SECURITY STEP) ---
    
    # UPDATE: Search using generated_id
    linked_permission = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.generated_id == booking_data.permission_letter_id
    ).first()

    if not linked_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Permission letter not found or invalid ID."
        )
        
    if linked_permission.club_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You cannot book a venue using another club's permission letter."
        )
        
    # NEW: Ensure the letter is actually approved before letting them book!
    if linked_permission.status != "Approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="This permission letter has not been fully approved yet."
        )

    # --- 3. Concurrency / Conflict Check ---
    # Double-check that no one booked the room 
    conflict = db.query(models.VenueBooking).filter(
        models.VenueBooking.date == booking_data.date,
        models.VenueBooking.time == booking_data.time,
        models.VenueBooking.room_id == booking_data.room_id,
        # UPDATE: Match the availability list here too
        models.VenueBooking.status.in_([
            "Pending GenSec", 
            "Pending President", 
            "Pending FacAd", 
            "Pending ADSA", 
            "Approved"
        ])
    ).first()
    
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="The selected room has just been booked for the given date and time."
        )
    
    # --- 4. Database Insertion ---
    new_booking = models.VenueBooking(
        date=booking_data.date,
        time=booking_data.time,
        room_id=booking_data.room_id,
        event_title=booking_data.event_title,
        event_type=booking_data.event_type,
        expected_attendees=booking_data.expected_attendees,
        description=booking_data.description,               # <--- Nice and clean!
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

