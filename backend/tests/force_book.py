from app.database import SessionLocal
from app.models import Room, VenueBooking

def inject_booking():
    db = SessionLocal()
    
    # Find L-20
    l20 = db.query(Room).filter(Room.name == "L-20").first()
    
    if not l20:
        print("Error: L-20 not found in database!")
        return

    # Create the overlapping booking
    overlap = VenueBooking(
        date="2026-10-05",
        time="09:00 AM - 11:00 AM",
        room_id=l20.id,
        event_title="UI Test",
        status="Approved" # Must be Approved or Pending to trigger the overlap!
    )
    
    db.add(overlap)
    db.commit()
    print("✅ SUCCESS: Dummy booking forcefully injected into database!")

if __name__ == "__main__":
    inject_booking()