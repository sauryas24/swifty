from app.database import SessionLocal
from app.models import User, Room, MoURequest, PermissionLetter, VenueBooking

def seed_history():
    db = SessionLocal()
    
    # 1. Fetch our Music Club coordinator
    coordinator = db.query(User).filter(User.role == "coordinator").first()
    if not coordinator:
        print("❌ Error: No coordinator found. Run your user seed script first!")
        db.close()
        return

    # 2. Fetch or create a couple of rooms for the venue bookings
    room1 = db.query(Room).first()
    if not room1:
        room1 = Room(name="LHC L-17", capacity=120)
        db.add(room1)
        db.commit()

    print("Past Requests for the Music Club...")

    # --- Step 1: Seed MoUs ---
    # Note: Because your MoU model lacks a 'date' column, we will just add them. 
    # Your router safely handles this with getattr(mou, 'date', 'N/A')!
    mou1 = MoURequest(
        coordinator_id=coordinator.id,
        organization_name="Sponsorship with Brand-X",
        purpose="Fest Sponsorship",
        document_url="static/docs/brand_x.pdf",
        status="Approved"
    )
    mou2 = MoURequest(
        coordinator_id=coordinator.id,
        organization_name="Media Coverage Partner",
        purpose="Campus Media",
        document_url="static/docs/media.pdf",
        status="Approved"
    )
    db.add_all([mou1, mou2])

    # --- Step 2: Seed Permission Letters ---
    pl1 = PermissionLetter(
        event_name="Outdoor Speaker setup at OAT",
        date="Feb 12, 2026", # Formatted to match your UI mockups
        time="18:00",
        reason="Acoustic Night",
        club_id=coordinator.id,
        status="Rejected",
        comments="Please ensure the Faculty-in-Charge has signed the latest security clearance form."
    )
    pl2 = PermissionLetter(
        event_name="Night Performance Extension",
        date="Feb 01, 2026",
        time="22:00",
        reason="Late night practice",
        club_id=coordinator.id,
        status="Pending GenSec"
    )
    db.add_all([pl1, pl2])
    db.commit() # We must commit here so pl1 and pl2 get their auto-generated IDs!

    # --- Step 3: Seed Venue Bookings (Linked to the Permission Letters!) ---
    vb1 = VenueBooking(
        date="Feb 08, 2026",
        time="14:00",
        room_id=room1.id,
        event_title="LHC L-17 Vocal Workshop",
        event_type="Workshop",
        expected_attendees=50,
        description="Vocal training",
        permission_letter_id=str(pl2.id), # Linking to the PL we just made so the router finds it!
        status="Pending GenSec"
    )
    vb2 = VenueBooking(
        date="Jan 28, 2026",
        time="18:00",
        room_id=room1.id,
        event_title="Auditorium Main Stage",
        event_type="Performance",
        expected_attendees=500,
        description="Main event",
        permission_letter_id=str(pl1.id), # Linking to the other PL!
        status="Rejected",
        comments="Venue is already booked for a faculty conference."
    )
    db.add_all([vb1, vb2])
    db.commit()

    print(f"✅ Success! Generated a rich history of MoUs, Permissions, and Venue Bookings for {coordinator.username}.")
    db.close()

if __name__ == "__main__":
    seed_history()