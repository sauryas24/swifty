from app.database import SessionLocal
from app.models import Club, Transaction
import datetime

def seed_finances():
    # Open a connection to the database
    db = SessionLocal()
    
    # 1. Check if clubs exist, if not, create them
    if db.query(Club).count() == 0:
        print("Adding sample clubs to the database...")
        clubs_to_add = [
            Club(name="Music Club", total_allocated=500000.0, total_spent=0.0),
            Club(name="Dance Club", total_allocated=300000.0, total_spent=0.0)
        ]
        db.add_all(clubs_to_add)
        db.commit()
    
    # Fetch the Music Club to attach transactions to it
    music_club = db.query(Club).filter(Club.name == "Music Club").first()

    # 2. Check if transactions exist to avoid spamming the database
    if db.query(Transaction).count() == 0 and music_club:
        print("Adding sample finance transactions to the Music Club...")
        
        # Creating dummy transactions based on the UI mockups in the Design Doc
        transactions_to_add = [
            Transaction(
                club_id=music_club.id,
                amount=15000.0,
                description="New PA System Rental",
                receipt_url="static/receipts/dummy_pa_system.pdf",
                timestamp=datetime.datetime.utcnow()
            ),
            Transaction(
                club_id=music_club.id,
                amount=4500.0,
                description="Guitar Strings & Repairs",
                receipt_url="static/receipts/dummy_guitar_strings.pdf",
                timestamp=datetime.datetime.utcnow()
            )
        ]
        
        db.add_all(transactions_to_add)
        
        # 3. Update the total_spent for the Music Club!
        total_dummy_spent = sum([t.amount for t in transactions_to_add])
        music_club.total_spent += total_dummy_spent
        
        db.commit()
        print(f"✅ Success! Sample transactions added. Music Club total spent updated to ₹{music_club.total_spent}")
    else:
        print("Clubs and Transactions already exist. Skipping.")
        
    db.close()

if __name__ == "__main__":
    seed_finances()