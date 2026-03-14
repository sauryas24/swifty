from app.database import SessionLocal
from app.models import Room

def seed_rooms():
    # Open a connection to the database
    db = SessionLocal()
    
    # Check if we already have rooms to avoid adding duplicates
    if db.query(Room).count() == 0:
        print("Adding rooms to the database...")
        rooms_to_add = [
            Room(name="L-20", capacity=150),
            Room(name="L-18", capacity=100),
            Room(name="OAT Main Stage", capacity=800),
            Room(name="LHC L-17", capacity=120)
        ]
        
        # Add them all at once and save
        db.add_all(rooms_to_add)
        db.commit()
        print("Success! Venues added.")
    else:
        print("Venues already exist in the database. Skipping.")
        
    db.close()

if __name__ == "__main__":
    seed_rooms()