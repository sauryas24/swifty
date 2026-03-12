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