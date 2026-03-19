from app.database import SessionLocal
from app.models import Room, VenueBooking # <-- Make sure VenueBooking is imported!

def seed_database():
    db = SessionLocal()
    
    # 1. Add Rooms (You already have this!)
    if db.query(Room).count() == 0:
        print("Adding rooms to the database...")
        rooms_to_add = [
            Room(name="L-20", capacity=60),
            Room(name="L-18", capacity=45),
            Room(name="L-19", capacity=45),
            Room(name="LHC Main", capacity=400)
        ]
        db.add_all(rooms_to_add)
        db.commit()
        print("Success! Venues added.")

    # 2. ADD THIS NEW BLOCK: Create a fake booking to test unavailability
    # We will check if it exists first so we don't add it twice
    if db.query(VenueBooking).count() == 0:
        print("Adding a dummy booking to test unavailable rooms...")
        
        # We need the ID of L-20 so we can book it. 
        l20_room = db.query(Room).filter(Room.name == "L-20").first()
        
        dummy_booking = VenueBooking(
            date="2026-10-05",                 # Must exactly match frontend format
            time="02:00 PM - 04:00 PM",        # Must exactly match frontend button text
            room_id=l20_room.id,
            event_title="Test Overlap Event",
            event_type="Workshop",
            expected_attendees=50,
            description="Testing the unavailable rooms UI",
            permission_letter_id="PL-TEST-001",
            status="Approved"                  # A status that triggers the conflict check!
        )
        
        db.add(dummy_booking)
        db.commit()
        print("Success! Dummy booking added.")

if __name__ == "__main__":
    seed_database()