from pydantic import BaseModel, ConfigDict
from typing import List
from typing import List, Optional
from datetime import datetime

# 1. How we send room details to the frontend
class RoomInfo(BaseModel):
    id: int
    name: str
    capacity: int

    model_config = ConfigDict(from_attributes=True)

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
    id : int
    username: str
    access_token: str
    token_type: str
    role: str       # We send the role back so the frontend knows which dashboard to load.   

class TransactionBase(BaseModel):
    amount: float
    description: str

class TransactionCreate(TransactionBase):
    club_id: int

class TransactionRead(TransactionBase):
    id: int
    timestamp: datetime
    receipt_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ClubFinanceStatus(BaseModel):
    name: str
    total_allocated: float
    total_spent: float
    remaining_balance: float # total_allocated - total_spent
    utilization_percentage: float # (total_spent / total_allocated) * 100
    transactions: List[TransactionRead]
    
    model_config = ConfigDict(from_attributes=True)
    
class PermissionLetterCreate(BaseModel):
    event_name: str
    date: str
    time: str
    reason: str

class PermissionLetterResponse(BaseModel):
    id: int
    event_name: str
    date: str
    time: str
    reason: str
    club_id: int
    status: str
    generated_id: Optional[str] = None   # Populated once fully approved

    # Using the clean V2 syntax we fixed earlier!
    model_config = ConfigDict(from_attributes=True)
class AnnouncementCreate(BaseModel):
    message: str
    heading: str 
    target_clubs: Optional[List[str]] = None
    # Example: ["robotics", "coding", "drama"]


# What the backend returns when sending announcements to frontend
class AnnouncementResponse(BaseModel):
    id: int
    sender_username: str
    heading: str
    message: str
    target_clubs: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class MoUCreate(BaseModel):
    organization_name: str
    purpose: str
    document_url: str

class MoUResponse(BaseModel):
    id: int
    organization_name: str
    purpose: str
    document_url: str
    status: str
    comments: Optional[str]

    model_config = ConfigDict(from_attributes=True)

# --- Schemas ---
class ApprovalAction(BaseModel):
    action: str  # Must be "approve" or "reject"
    message: Optional[str] = None  # Optional reason for rejection
    otp_code: Optional[str] = None
# Used when an authority clicks "Reject"
class RejectionCreate(BaseModel):
    reason: str

class CalendarEventResponse(BaseModel):
    id: int
    date: str
    time: str
    event_title: str
    event_type: str
    venue_name: str

    model_config = ConfigDict(from_attributes=True)

# Add this to app/schemas.py
class RequestRecordResponse(BaseModel):
    id: int
    type: str       
    date: str       # Submission date (created_at)
    details: str    
    status: str     
    raw_status: str 
    comments: Optional[str] = None
    generated_id: Optional[str] = None
    
    # --- NEW EXTENDED DETAIL FIELDS ---
    purpose: Optional[str] = None
    document_url: Optional[str] = None
    event_date: Optional[str] = None # The date of the actual event
    time: Optional[str] = None
    reason: Optional[str] = None
    expected_attendees: Optional[int] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    
    
# When the user types their email and clicks "Send OTP"
class OTPRequest(BaseModel):
    email_id: str

# When the user types the 6-digit code and clicks "Verify"
class OTPVerify(BaseModel):
    email_id: str
    otp_code: str    


