from pydantic import BaseModel
from typing import List
from typing import List, Optional
from datetime import datetime

# 1. How we send room details to the frontend
class RoomInfo(BaseModel):
    id: int
    name: str
    capacity: int

    class Config:
        from_attributes = True

# 2. The response for the Availability Check
class AvailabilityResponse(BaseModel):
    available_rooms: List[RoomInfo]
    unavailable_rooms: List[RoomInfo]

# 3. What the frontend MUST send when submitting the final form
class BookingCreate(BaseModel):
    date: str
    time: str
    room_id: int
    event_title: str
    event_type: str
    expected_attendees: int
    description: str
    permission_letter_id: str
    
    
# What the frontend sends
class LoginRequest(BaseModel):
    email_id: str
    password: str

# What the backend replies with
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str       # We send the role back so the frontend knows which dashboard to load.   


class PermissionLetterCreate(BaseModel):
    event_name: str
    date: str
    time: str
    reason: str

# What the backend sends back after successful submission
class PermissionLetterResponse(BaseModel):
    id: int               # The generated Permission Letter ID
    event_name: str
    status: str
    
    class Config:
        from_attributes = True    

# What the frontend sends when publishing an announcement
class AnnouncementCreate(BaseModel):
    message: str
    target_clubs: Optional[List[str]] = None
    # Example: ["robotics", "coding", "drama"]


# What the backend returns when sending announcements to frontend
class AnnouncementResponse(BaseModel):
    id: int
    sender_id: int
    message: str
    target_clubs: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

