import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal, engine
from backend.app.models import (
    Base, User, Club, Room, VenueBooking, 
    Transaction, PermissionLetter, Announcement, MoURequest
)
from backend.app.utils.security import get_password_hash

def seed_database():
    print("🔍 Checking database tables...")
    
    # Safely creates only MISSING tables. Does not overwrite existing ones.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. SAFELY SEED ROOMS / VENUES
        if not db.query(Room).first():
            print("Seeding Rooms")
            rooms = [
                Room(name="Main Auditorium", capacity=1200),
                Room(name="OAT (Open Air Theater)", capacity=1500),
                Room(name="L17", capacity=400),
                Room(name="L7", capacity=150),
                Room(name="Student Activity Center (SAC)", capacity=300)
            ]
            db.add_all(rooms)
            db.commit()
            print("Rooms seeded successfully.")
        else:
            print("Rooms already exist. Skipping.")

        # 2. SAFELY SEED USERS
        if not db.query(User).first():
            print("Seeding Users (Coordinators & Authorities)...")
            
            users = [
                # Coordinators
                User(username="Music Club", email_id="gymkhana.swifty@gmail.com", password=get_password_hash("music123"), role="coordinator", associate_council="Cultural"),
                User(username="Dance Club", email_id="dance@iitk.ac.in", password=get_password_hash("dance123"), role="coordinator", associate_council="Cultural"),
                User(username="Programming Club", email_id="pclub@iitk.ac.in", password=get_password_hash("pclub123"), role="coordinator", associate_council="Science & Tech"),
                User(username="Robotics Club", email_id="robotics@iitk.ac.in", password=get_password_hash("robot123"), role="coordinator", associate_council="Science & Tech"),
                
                # Authorities (Approval Chain)
                User(username="General Secretary", email_id="gensec.swifty@gmail.com", password=get_password_hash("admin123"), role="gensec", associate_council="Cultural"),
                User(username="President SG", email_id="psg.swifty@gmail.com", password=get_password_hash("admin123"), role="president"),
                User(username="Faculty Advisor", email_id="facad.swifty@gmail.com", password=get_password_hash("admin123"), role="facad"),
                User(username="ADSA", email_id="adsa.swifty@gmail.com", password=get_password_hash("admin123"), role="adsa")
            ]
            db.add_all(users)
            db.commit()
            print("Users seeded successfully.")
        else:
            print("Users already exist. Skipping.")

        # ==========================================
        # 3. SAFELY SEED CLUBS (Attached to Users)
        # ==========================================
        if not db.query(Club).first():
            print("🎪 Seeding Clubs & Budgets...")
            
            # Fetch users to link correctly
            u_music = db.query(User).filter(User.username == "Music Club").first()
            u_dance = db.query(User).filter(User.username == "Dance Club").first()
            u_pclub = db.query(User).filter(User.username == "Programming Club").first()
            u_robotics = db.query(User).filter(User.username == "Robotics Club").first()

            clubs = [
                Club(name="Music Club", email="music@iitk.ac.in", user_id=u_music.id, total_allocated=350000.0, total_spent=50000.0),
                Club(name="Dance Club", email="dance@iitk.ac.in", user_id=u_dance.id, total_allocated=400000.0, total_spent=0.0),
                Club(name="Programming Club", email="pclub@iitk.ac.in", user_id=u_pclub.id, total_allocated=150000.0, total_spent=25000.0),
                Club(name="Robotics Club", email="robotics@iitk.ac.in", user_id=u_robotics.id, total_allocated=800000.0, total_spent=120000.0)
            ]
            db.add_all(clubs)
            db.commit()
            print("✅ Clubs seeded successfully.")
        else:
            print("⏭️  Clubs already exist. Skipping.")

        # ==========================================
        # 4. SAFELY SEED TRANSACTIONS
        # ==========================================
        if not db.query(Transaction).first():
            print("💸 Seeding Financial Transactions...")
            
            c_music = db.query(Club).filter(Club.name == "Music Club").first()
            c_pclub = db.query(Club).filter(Club.name == "Programming Club").first()
            c_robotics = db.query(Club).filter(Club.name == "Robotics Club").first()

            transactions = [
                Transaction(club_id=c_music.id, amount=50000.0, description="Purchase of new drum kit and amplifiers", receipt_url="receipts/drums.pdf"),
                Transaction(club_id=c_pclub.id, amount=25000.0, description="AWS Server Hosting for Swifty deployment", receipt_url="receipts/aws_bill.pdf"),
                Transaction(club_id=c_robotics.id, amount=120000.0, description="Raspberry Pi kits and motor controllers", receipt_url="receipts/hardware.pdf")
            ]
            db.add_all(transactions)
            db.commit()
            print("✅ Transactions seeded successfully.")
        else:
            print("⏭️  Transactions already exist. Skipping.")

        # ==========================================
        # 5. SAFELY SEED PERMISSION LETTERS
        # ==========================================
        if not db.query(PermissionLetter).first():
            print("📝 Seeding Permission Letters...")
            
            u_music = db.query(User).filter(User.username == "Music Club").first()
            u_dance = db.query(User).filter(User.username == "Dance Club").first()
            u_pclub = db.query(User).filter(User.username == "Programming Club").first()

            letters = [
                # Approved Letter
                PermissionLetter(event_name="Acoustic Night 2026", date="2026-05-15", time="18:00", reason="Annual unplugged music festival.", club_id=u_music.id, status="Approved", generated_id="PL-2026-0001"),
                # Pending Letters in different stages
                PermissionLetter(event_name="Summer Dance Showcase", date="2026-05-20", time="19:00", reason="End of semester dance performance.", club_id=u_dance.id, status="Pending GenSec"),
                PermissionLetter(event_name="Hackathon - CodeRed", date="2026-06-10", time="09:00", reason="24-hour campus hackathon.", club_id=u_pclub.id, status="Pending ADSA"),
                # Rejected Letter
                PermissionLetter(event_name="Midnight Jam", date="2026-04-25", time="23:59", reason="Late night music jam session.", club_id=u_music.id, status="Rejected", comments="Curfew rules do not permit events past 11:00 PM without special DOSA clearance.")
            ]
            db.add_all(letters)
            db.commit()
            print("✅ Permission Letters seeded successfully.")
        else:
            print("⏭️  Permission Letters already exist. Skipping.")

        # ==========================================
        # 6. SAFELY SEED VENUE BOOKINGS
        # ==========================================
        if not db.query(VenueBooking).first():
            print("📅 Seeding Venue Bookings...")
            
            r_auditorium = db.query(Room).filter(Room.name == "Main Auditorium").first()
            r_l17 = db.query(Room).filter(Room.name == "L17 (Lecture Hall)").first()

            bookings = [
                # Booking tied to the approved permission letter
                VenueBooking(date="2026-05-15", time="06:00 PM - 08:00 PM", room_id=r_auditorium.id, event_title="Acoustic Night 2026", event_type="Official Performance", expected_attendees=800, description="Need extra stage monitors and lighting setup.", permission_letter_id="PL-2026-0001", status="Approved"),
                # Pending booking
                VenueBooking(date="2026-06-10", time="09:00 AM - 11:00 AM", room_id=r_l17.id, event_title="Hackathon Opening Ceremony", event_type="Meeting", expected_attendees=350, description="Need projector and mic.", permission_letter_id="PL-2026-0002", status="Pending ADSA")
            ]
            db.add_all(bookings)
            db.commit()
            print("✅ Venue Bookings seeded successfully.")
        else:
            print("⏭️  Venue Bookings already exist. Skipping.")

        # ==========================================
        # 7. SAFELY SEED MOU REQUESTS
        # ==========================================
        if not db.query(MoURequest).first():
            print("🤝 Seeding MoU Requests...")
            
            u_robotics = db.query(User).filter(User.username == "Robotics Club").first()

            mous = [
                MoURequest(coordinator_id=u_robotics.id, organization_name="TechCorp India", purpose="Sponsorship of ₹2,000,000 for building a Mars Rover prototype. They require logo placement on our team shirts.", document_url="mou_drafts/techcorp.pdf", status="Pending GenSec")
            ]
            db.add_all(mous)
            db.commit()
            print("✅ MoU Requests seeded successfully.")
        else:
            print("⏭️  MoU Requests already exist. Skipping.")

        # ==========================================
        # 8. SAFELY SEED ANNOUNCEMENTS
        # ==========================================
        if not db.query(Announcement).first():
            print("📢 Seeding Announcements...")
            
            gensec = db.query(User).filter(User.username == "General Secretary").first()
            adsa = db.query(User).filter(User.username == "ADSA").first()

            announcements = [
                Announcement(sender_id=gensec.id, heading="Welcome to Swifty!", message="The new Gymkhana workflow automation portal is now live. Please submit all upcoming venue requests through this system.", target_clubs="All"),
                Announcement(sender_id=adsa.id, heading="Budget Utilization Deadline", message="All clubs must utilize at least 50% of their allocated budget by the mid-semester evaluation. Ensure your transaction receipts are uploaded.", target_clubs="All")
            ]
            db.add_all(announcements)
            db.commit()
            print("✅ Announcements seeded successfully.")
        else:
            print("⏭️  Announcements already exist. Skipping.")

    except Exception as e:
        print(f"\n❌ An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()