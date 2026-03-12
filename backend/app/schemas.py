from pydantic import BaseModel
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


class TransactionBase(BaseModel):
    amount: float
    description: str

class TransactionCreate(TransactionBase):
    club_id: int

class TransactionRead(TransactionBase):
    id: int
    timestamp: datetime
    receipt_url: Optional[str]

    class Config:
        from_attributes = True

class ClubFinanceStatus(BaseModel):
    name: str
    total_allocated: float
    total_spent: float
    remaining_balance: float # total_allocated - total_spent
    utilization_percentage: float # (total_spent / total_allocated) * 100
    transactions: List[TransactionRead]

    class Config:
        from_attributes = True