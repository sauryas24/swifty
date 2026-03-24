import sys
import os
import datetime

# Tell Python to look in the parent folder for the 'app' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import (
    Base, User, Room, VenueBooking, Club, 
    Transaction, PermissionLetter, MoURequest, OTP, Announcement
)
from app.utils.security import get_password_hash

def master_seed():
    print("🧹 Destroying old corrupted tables...")
    Base.metadata.drop_all(bind=engine)

    print("🏗️ Building fresh, updated tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # ==========================================
        # 1. SEED USERS
        # ==========================================
        print("👤 Seeding Users...")
        coordinator = User(
            username="Music Club",
            email_id="vanshikaag24@iitk.ac.in",
            password=get_password_hash("music123"),
            role="coordinator"
        )
        gensec = User(
            username="General Secretary",
            email_id="gensec@iitk.ac.in",
            password=get_password_hash("admin123"),
            role="authority"
        )
        db.add_all([coordinator, gensec])
        db.commit()

        # ==========================================
        # 2. SEED ROOMS
        # ==========================================
        print("🏢 Seeding Rooms...")
        rooms = [
            Room(name="L-20", capacity=60),
            Room(name="L-18", capacity=45),
            Room(name="L-19", capacity=45),
            Room(name="LHC Main", capacity=400),
            Room(name="LHC L-17", capacity=120),
            Room(name="Main Stadium", capacity=1000) # Added for calendar tests!
        ]
        db.add_all(rooms)
        db.commit()

        # ==========================================
        # 3. SEED FINANCES & TRANSACTIONS
        # ==========================================
        print("💰 Seeding Finances...")
        music_ledger = Club(
            user_id=coordinator.id, 
            name="Music Club", 
            total_allocated=500000.0, 
            total_spent=19500.0
        )
        dance_ledger = Club(name="Dance Club", total_allocated=300000.0, total_spent=0.0)
        db.add_all([music_ledger, dance_ledger])
        db.commit()

        transactions = [
            Transaction(
                club_id=music_ledger.id,
                amount=15000.0,
                description="New PA System Rental",
                receipt_url="static/receipts/dummy_pa_system.pdf",
                timestamp=datetime.datetime.now(datetime.UTC)
            ),
            Transaction(
                club_id=music_ledger.id,
                amount=4500.0,
                description="Guitar Strings & Repairs",
                receipt_url="static/receipts/dummy_guitar_strings.pdf",
                timestamp=datetime.datetime.now(datetime.UTC)
            )
        ]
        db.add_all(transactions)
        db.commit()

        # ==========================================
        # 4. SEED MoU REQUESTS
        # ==========================================
        print("🤝 Seeding MoUs...")
        mous = [
            MoURequest(
                coordinator_id=coordinator.id,
                organization_name="Brand-X",
                purpose="Sponsorship with Brand-X",
                document_url="static/docs/dummy_brand_x_mou.pdf",
                status="Approved"
            ),
            MoURequest(
                coordinator_id=coordinator.id,
                organization_name="Media Coverage Partner",
                purpose="Media Coverage for upcoming fest",
                document_url="static/docs/dummy_media_mou.pdf",
                status="Pending Gensec" 
            ),
            MoURequest(
                coordinator_id=coordinator.id,
                organization_name="Local Sound Rentals",
                purpose="Annual Audio Equipment Supply",
                document_url="static/docs/dummy_audio_mou.pdf",
                status="Rejected",
                comments="Please revise the payment terms as per DOSA guidelines."
            )
        ]
        db.add_all(mous)
        db.commit()

        # ==========================================
        # 5. SEED PERMISSION LETTERS
        # ==========================================
        print("📝 Seeding Permission Letters...")
        letters = [
            PermissionLetter(event_name="Annual Music Showcase", date="2026-04-10", time="18:00", reason="End of semester performance", club_id=coordinator.id, status="Pending GenSec"),
            PermissionLetter(event_name="Workshop on Music Production", date="2026-04-15", time="14:00", reason="Digital tools workshop", club_id=coordinator.id, status="Pending FacAd"),
            PermissionLetter(event_name="Inter-College Jam Session", date="2026-04-20", time="16:00", reason="Collaborative event", club_id=coordinator.id, status="Pending ADSA"),
            PermissionLetter(event_name="Acoustic Night", date="2026-03-25", time="19:00", reason="Unplugged performances", club_id=coordinator.id, status="Approved", generated_id="PL-2026-0001"),
            PermissionLetter(event_name="Midnight Concert", date="2026-03-30", time="23:00", reason="Late night music concert", club_id=coordinator.id, status="Rejected", comments="Events cannot be held after 10 PM as per institute policy.")
        ]
        db.add_all(letters)
        db.commit()

        # ==========================================
        # 6. SEED VENUE BOOKINGS
        # ==========================================
        print("📅 Seeding Venue Bookings...")
        l20_id = next(r.id for r in rooms if r.name == "L-20")
        l18_id = next(r.id for r in rooms if r.name == "L-18")
        stadium_id = next(r.id for r in rooms if r.name == "Main Stadium")
        
        bookings = [
            # The Overlap Test
            VenueBooking(date="2026-10-05", time="02:00 PM - 04:00 PM", room_id=l20_id, event_title="UI Overlap Test", event_type="Workshop", expected_attendees=50, description="Testing UI", permission_letter_id="PL-TEST-001", status="Approved"),
            
            # Standard Bookings
            VenueBooking(date="2026-03-20", time="18:00-20:00", room_id=l18_id, event_title="Acoustic Night", event_type="Cultural", expected_attendees=150, description="Unplugged music", permission_letter_id="PL-2026-0001", status="Pending GenSec"),
            VenueBooking(date="2026-03-25", time="14:00-17:00", room_id=l20_id, event_title="CP Bootcamp", event_type="Academic", expected_attendees=80, description="Graph theory", permission_letter_id="PL-2026-002", status="Approved"),
            VenueBooking(date="2026-03-28", time="10:00-12:00", room_id=l18_id, event_title="Flash Mob", event_type="Cultural", expected_attendees=300, description="Surprise dance event", permission_letter_id="PL-2026-003", status="Rejected by DOSA", comments="Will disrupt classes."),
            
            # Calendar Test Bookings!
            VenueBooking(date="2026-04-10", time="10:00 AM", room_id=stadium_id, event_title="Secret Club Meeting", event_type="Meeting", expected_attendees=20, description="Confidential", permission_letter_id="PL-2026-004", status="Pending FacAd"),
            VenueBooking(date="2026-04-15", time="06:30 AM", room_id=stadium_id, event_title="Sports Trials", event_type="Athletics", expected_attendees=100, description="Varsity team trials", permission_letter_id="PL-2026-005", status="Approved")
        ]
        db.add_all(bookings)
        db.commit()

        print("\n🚀 🚀 🚀 MASTER SEED COMPLETE! The Swifty Database is fully loaded. 🚀 🚀 🚀\n")

    except Exception as e:
        print(f"\n❌ An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    master_seed()