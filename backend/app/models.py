from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import datetime


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email_id = Column(String, unique=True, index=True)
    password = Column(String)  # This will store the hashed password
    role = Column(String)      # "coordinator" or "authority"
    associate_council = Column(String, nullable=True)
    
    

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  
    capacity = Column(Integer)

class VenueBooking(Base):
    __tablename__ = "venue_bookings"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)       
    time = Column(String, index=True)       
    room_id = Column(Integer, ForeignKey("rooms.id"))
    
    # Event Details
    event_title = Column(String)
    event_type = Column(String)
    expected_attendees = Column(Integer)
    description = Column(String)
    permission_letter_id = Column(String)   # This will be provided to the user after the permission letter is approved.
    
    status = Column(String, default="Pending FacAd") # Starts the approval chain
    
    # Links the booking to the actual room details
    room = relationship("Room")

class Club(Base):
    __tablename__ = "clubs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    total_allocated = Column(Float, default=500000.0) # From HTML: ₹5,00,000
    total_spent = Column(Float, default=0.0)
    
    transactions = relationship("Transaction", back_populates="club")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"))
    amount = Column(Float) # Amount (₹) 
    description = Column(String) # Description
    receipt_url = Column(String, nullable=True) # File attachment path 
    timestamp = Column(DateTime, default=datetime.datetime.utcnow) # For log history 
    
    club = relationship("Club", back_populates="transactions")
    
class PermissionLetter(Base):
    __tablename__ = "permission_letters"

    id = Column(Integer, primary_key=True, index=True)
    
    # user-provided details
    event_name = Column(String, index=True)
    date = Column(String)
    time = Column(String)
    reason = Column(String)
    
    # Attached automatically by the backend
    club_id = Column(Integer, ForeignKey("users.id"))
    
    # The Approval Tracker
    status = Column(String, default="Pending GenSec") 
    #in case of rejection
    rejection_comment = Column(String, nullable=True)
    
    # Relationship to fetch club details 
    club = relationship("User")

