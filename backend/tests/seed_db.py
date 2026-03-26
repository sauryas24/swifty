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
        # Coordinators
        coordinator_music = User(username="Music Club", email_id="vanshikaag24@iitk.ac.in", password=get_password_hash("music123"), role="coordinator")
        coordinator_dance = User(username="Dance Club", email_id="dance@iitk.ac.in", password=get_password_hash("dance123"), role="coordinator")
        coordinator_drama = User(username="Dramatics Club", email_id="drama@iitk.ac.in", password=get_password_hash("drama123"), role="coordinator")
        coordinator_prog = User(username="Programming Club", email_id="prog@iitk.ac.in", password=get_password_hash("prog123"), role="coordinator")
        
        # Authorities
        gensec = User(username="General Secretary", email_id="mharsh24@iitk.ac.in", password=get_password_hash("admin123"), role="gensec")
        president = User(username="President Gymkhana", email_id="hmalgatte@gmail.com", password=get_password_hash("psg123"), role="president")
        facad = User(username="Faculty Advisor", email_id="vanshikaagrawal1901@gmail.com", password=get_password_hash("admin123"), role="facad")
        adsa = User(username="ADSA", email_id="vanshikaagrawal868@gmail.com", password=get_password_hash("admin123"), role="adsa")
        dosa = User(username="DOSA", email_id="sreejas24@iitk.ac.in", password=get_password_hash("admin123"), role="dosa")

        db.add_all([
            coordinator_music, coordinator_dance, coordinator_drama, coordinator_prog, 
            gensec, president, facad, adsa, dosa
        ])
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
            Room(name="Main Stadium", capacity=1000)
        ]
        db.add_all(rooms)
        db.commit()

        # ==========================================
        # 3. SEED FINANCES & TRANSACTIONS
        # ==========================================
        print("💰 Seeding Finances...")
        # By creating them in this exact order, they get IDs 1, 2, 3, 4 to match your HTML sidebar!
        music_ledger = Club(user_id=coordinator_music.id, name="Music Club", total_allocated=500000.0, total_spent=0)
        dance_ledger = Club(user_id=coordinator_dance.id, name="Dance Club", total_allocated=300000.0, total_spent=0)
        drama_ledger = Club(user_id=coordinator_drama.id, name="Dramatics Club", total_allocated=400000.0, total_spent=0)
        prog_ledger = Club(user_id=coordinator_prog.id, name="Programming Club", total_allocated=250000.0, total_spent=0)
        
        db.add_all([music_ledger, dance_ledger, drama_ledger, prog_ledger])
        db.commit()

        # transactions = [
        #     Transaction(club_id=music_ledger.id, amount=15000.0, description="New PA System Rental", timestamp=datetime.datetime.now(datetime.UTC)),
        #     Transaction(club_id=music_ledger.id, amount=4500.0, description="Guitar Strings & Repairs", timestamp=datetime.datetime.now(datetime.UTC)),
        #     Transaction(club_id=drama_ledger.id, amount=12000.0, description="Stage Props & Costumes", timestamp=datetime.datetime.now(datetime.UTC)),
        #     Transaction(club_id=dance_ledger.id, amount=45000.0, description="Annual Choreographer Fee", timestamp=datetime.datetime.now(datetime.UTC)),

        #     Transaction(
        #         club_id=music_ledger.id,
        #         amount=15000.0,
        #         description="New PA System Rental",
        #         receipt_url="static/receipts/dummy_pa_system.pdf",
        #         timestamp=datetime.datetime.now(datetime.timezone.utc)
        #     ),
        #     Transaction(
        #         club_id=music_ledger.id,
        #         amount=4500.0,
        #         description="Guitar Strings & Repairs",
        #         receipt_url="static/receipts/dummy_guitar_strings.pdf",
        #         timestamp=datetime.datetime.now(datetime.timezone.utc)
        #     )
 
        # ]
        # db.add_all(transactions)
        # db.commit()

        # ==========================================
        # 4. SEED MoU REQUESTS
        # ==========================================
        # print("🤝 Seeding MoUs...")
        # mous = [
        #     MoURequest(coordinator_id=coordinator_music.id, organization_name="Brand-X", purpose="Sponsorship with Brand-X", document_url="static/docs/dummy_brand_x.pdf", status="Approved"),
        #     MoURequest(coordinator_id=coordinator_dance.id, organization_name="Red Bull", purpose="Beverage Sponsorship", document_url="static/docs/dummy_redbull.pdf", status="Pending GenSec"),
        #     MoURequest(coordinator_id=coordinator_drama.id, organization_name="Local Sound Rentals", purpose="Audio Equipment Supply", document_url="static/docs/dummy_audio.pdf", status="Rejected", comments="Revise payment terms.")
        # ]
        # db.add_all(mous)
        # db.commit()

        # ==========================================
        # 5. SEED PERMISSION LETTERS
        # ==========================================
        # print("📝 Seeding Permission Letters...")
        # letters = [
        #     PermissionLetter(event_name="Annual Music Showcase", date="2026-04-10", time="18:00", reason="End of semester performance", club_id=coordinator_music.id, status="Pending GenSec"),
        #     PermissionLetter(event_name="Coding Hackathon", date="2026-04-15", time="14:00", reason="48-hour competitive programming", club_id=coordinator_prog.id, status="Pending FacAd"),
        #     PermissionLetter(event_name="Acoustic Night", date="2026-03-25", time="19:00", reason="Unplugged performances", club_id=coordinator_music.id, status="Approved", generated_id="PL-2026-0001"),
        # ]
        # db.add_all(letters)
        # db.commit()

        # ==========================================
        # 6. SEED VENUE BOOKINGS
        # ==========================================
        # print("📅 Seeding Venue Bookings...")
        # l20_id = next(r.id for r in rooms if r.name == "L-20")
        # l18_id = next(r.id for r in rooms if r.name == "L-18")
        # stadium_id = next(r.id for r in rooms if r.name == "Main Stadium")
        
        # bookings = [
        #     VenueBooking(date="2026-03-20", time="18:00-20:00", room_id=l18_id, event_title="Acoustic Night", event_type="Cultural", expected_attendees=150, description="Unplugged music", permission_letter_id="PL-2026-0001", status="Pending President"),
        #     VenueBooking(date="2026-04-15", time="06:30 AM", room_id=stadium_id, event_title="Sports Trials", event_type="Athletics", expected_attendees=100, description="Varsity team trials", permission_letter_id="PL-2026-005", status="Approved")
        # ]
        # db.add_all(bookings)
        # db.commit()

        # ==========================================
        # 7. SEED ANNOUNCEMENTS
        # ==========================================
        print("📢 Seeding Announcements...")
        announcements = [
            Announcement(
                sender_id=adsa.id,
                heading="URGENT: Semester Budget Audits",
                message="All clubs must upload their final ledger receipts by Friday 5PM to the finance module to avoid frozen accounts.",
                target_clubs="Music Club,Dance Club,Dramatics Club,Programming Club"
            ),
            Announcement(
                sender_id=president.id,
                heading="Gymkhana Election Code of Conduct",
                message="Please ensure no club activities clash with the upcoming election hustings schedule. Check the primary calendar.",
                target_clubs="Music Club,Dance Club,Dramatics Club,Programming Club"
            )
        ]
        db.add_all(announcements)
        db.commit()

        print("\n🚀 🚀 🚀 MASTER SEED COMPLETE! The Swifty Database is fully loaded. 🚀 🚀 🚀\n")

    except Exception as e:
        print(f"\n❌ An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    master_seed()