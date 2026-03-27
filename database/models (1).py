from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, validates
import datetime
import enum
from database import Base

# ==========================================
# 1. ENUMERATIONS (The Strict Rules)
# ==========================================

class UserRole(enum.Enum):
    COORDINATOR = "Coordinator"
    GENSEC = "GenSec"
    PSG = "PSG"
    FACAD = "FacAd"
    ADSA = "ADSA"

class RequestType(enum.Enum):
    VENUE_BOOKING = "Venue Booking"
    PERMISSION = "Permission Letter"
    MOU = "MoU"

class RequestStatus(enum.Enum):
    PENDING_GENSEC = "Pending with GenSec"
    PENDING_FACAD = "Pending with FacAd"
    PENDING_ADSA = "Pending with ADSA"
    APPROVED = "Approved"
    REJECTED = "Rejected"

# ==========================================
# 2. DATABASE MODELS (The Blueprints)
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    iitk_email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    @validates('iitk_email')
    def validate_email(self, key, address):
        if not address.endswith('@iitk.ac.in'):
            raise ValueError("Email must be a valid @iitk.ac.in address")
        return address

    # Relationships
    requests = relationship("ServiceRequest", back_populates="requester")


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    
    # Relationships
    requests = relationship("ServiceRequest", back_populates="venue")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    request_type = Column(Enum(RequestType), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING_GENSEC, nullable=False)
    
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=True)
    linked_permission_id = Column(Integer, ForeignKey("service_requests.id"), nullable=True)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    description = Column(String, nullable=True)
    is_public = Column(Boolean, default=False)

    # Relationships
    requester = relationship("User", back_populates="requests")
    venue = relationship("Venue", back_populates="requests")
    permission_letter = relationship("ServiceRequest", remote_side=[id])


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("service_requests.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING_GENSEC, nullable=False)
    comments = Column(String, nullable=True) 
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    request = relationship("ServiceRequest")
    approver = relationship("User")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    invoice_number = Column(String, unique=True, nullable=False)
    transaction_date = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    club = relationship("User")

# ==========================================
# EXTENSION TABLES (From Data Dictionary)
# ==========================================

class ClubCoordinator(Base):
    __tablename__ = "club_coordinators"

    id = Column(Integer, primary_key=True, index=True)
    # Links directly to the base User table
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Required attributes from the SRS Data Dictionary
    club_name = Column(String, unique=True, nullable=False)
    budget_allocated = Column(Float, default=0.0)
    budget_remaining = Column(Float, default=0.0)
    pending_bookings = Column(Integer, default=0)

    # Relationship back to the main user profile
    user = relationship("User", backref="coordinator_profile")


class Authority(Base):
    __tablename__ = "authorities"

    id = Column(Integer, primary_key=True, index=True)
    # Links directly to the base User table
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Required attributes from the SRS Data Dictionary
    designation = Column(String, nullable=False) # e.g., "Faculty In-Charge"
    digital_signature_token = Column(String, nullable=True)
    otp_secret = Column(String, nullable=True) # Used to verify the email OTPs

    user = relationship("User", backref="authority_profile")


# ==========================================
# COMMUNICATIONS TABLE
# ==========================================

class Announcement(Base):
    __tablename__ = "announcements"

    # Required attributes from the SRS Data Dictionary
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    
    # Since SQLite doesn't natively support arrays easily, we store target_clubs as a comma-separated string
    target_clubs = Column(String, nullable=True) 
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    sender = relationship("User")