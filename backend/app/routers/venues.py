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
        # We only care about bookings that are either pending or approved. 
        # If a booking was rejected, the room is technically free!
        models.VenueBooking.status.in_(["Pending FacAd", "Pending ADSA", "Approved"])
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
    # We must ensure the permission letter exists AND belongs to the logged-in club
    linked_permission = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.id == booking_data.permission_letter_id
    ).first()

    if not linked_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Permission letter not found."
        )
        
    if linked_permission.club_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You cannot book a venue using another club's permission letter."
        )

    # --- 3. Concurrency / Conflict Check ---
    # Double-check that no one booked the room in the milliseconds since the user checked availability
    conflict = db.query(models.VenueBooking).filter(
        models.VenueBooking.date == booking_data.date,
        models.VenueBooking.time == booking_data.time,
        models.VenueBooking.room_id == booking_data.room_id,
        models.VenueBooking.status.in_(["Pending FacAd", "Pending ADSA", "Approved"])
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
        description=booking_data.description,
        permission_letter_id=booking_data.permission_letter_id,
        status="Pending FacAd" # Standardize your starting states
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    return {
        "message": "Booking request submitted successfully!", 
        "booking_id": new_booking.id,
        "status": new_booking.status
    }

# ==========================================
# 3. GET MY BOOKINGS (Protected Route)
# ==========================================
# (Template for how you can fetch specific data for a single user in other routers)
@router.get("/my-bookings")
def get_my_venue_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Fetches all venue bookings associated with the currently logged-in user.
    """
    # 1. First get all permission letters owned by the user
    user_perm_ids = db.query(models.PermissionLetter.id).filter(
        models.PermissionLetter.club_id == current_user.id
    ).all()
    
    # Flatten the list of tuples returned by SQLAlchemy
    perm_id_list = [str(pid[0]) for pid in user_perm_ids]

    if not perm_id_list:
        return []

    # 2. Now get all venue bookings linked to those permission letters
    my_bookings = db.query(models.VenueBooking).filter(
        models.VenueBooking.permission_letter_id.in_(perm_id_list)
    ).all()

    return my_bookings