from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base



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
    
    # Relationship to fetch club details 
    club = relationship("User")