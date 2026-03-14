from app.database import SessionLocal
from app.models import VenueBooking, Room

def seed_venue_bookings():
    # Open a connection to the database
    db = SessionLocal()
    
    # 1. Fetch available rooms
    rooms = db.query(Room).all()
    
    # Safety Check: We cannot book a room if the rooms table is empty!
    if not rooms:
        print("❌ Error: No rooms found in the database.")
        print("Please run 'python seed.py' first to populate the lecture halls.")
        db.close()
        return

    # 2. Check if bookings already exist to avoid spamming the database
    if db.query(VenueBooking).count() == 0:
        print("Adding sample venue bookings to the database...")
        
        # We will use the first two rooms available in your database (e.g., L-20 and L-18)
        room_1_id = rooms[0].id
        room_2_id = rooms[1].id if len(rooms) > 1 else rooms[0].id
        
        bookings_to_add = [
            # A request that is waiting for approval
            VenueBooking(
                date="2026-03-20",
                time="18:00-20:00",
                room_id=room_1_id,
                event_title="Acoustic Night",
                event_type="Cultural",
                expected_attendees=150,
                description="An evening of unplugged music performances by the Music Club.",
                permission_letter_id="PL-2026-001",
                status="Pending GenSec"
            ),
            # A request that is already approved (Great for testing the public calendar!)
            VenueBooking(
                date="2026-03-25",
                time="14:00-17:00",
                room_id=room_2_id,
                event_title="Competitive Programming Bootcamp",
                event_type="Academic",
                expected_attendees=80,
                description="Introductory session to graph theory and dynamic programming.",
                permission_letter_id="PL-2026-002",
                status="Approved"
            ),
            # A request that was rejected
            VenueBooking(
                date="2026-03-28",
                time="10:00-12:00",
                room_id=room_1_id,
                event_title="Spontaneous Flash Mob",
                event_type="Cultural",
                expected_attendees=300,
                description="A surprise dance event during mid-semester break.",
                permission_letter_id="PL-2026-003",
                status="Rejected by DOSA"
            )
        ]
        
        # Add them all and save
        db.add_all(bookings_to_add)
        db.commit()
        print("✅ Success! Sample venue bookings added.")
    else:
        print("Venue bookings already exist. Skipping.")
        
    db.close()

if __name__ == "__main__":
    seed_venue_bookings()