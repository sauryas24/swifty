import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, User, Club # <--- Don't forget to import Club!
from app.utils.security import get_password_hash

def seed_database():
    print("🔍 Checking database tables...")
    
    # Safely creates only MISSING tables. Does not overwrite existing ones.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # ==========================================
        # 1. SAFELY SEED USERS (Independent Check)
        # ==========================================
        if db.query(User).first():
            print("⏭️  Users already exist. Skipping User creation.")
        else:
            print("👤 Restoring Users...")
            coordinator_music = User(username="Music Club", email_id="gymkhana.swifty@gmail.com", password=get_password_hash("music123"), role="coordinator")
            #coordinator_dance = User(username="Dance Club", email_id="gymkhana.swifty@gmail.com", password=get_password_hash("dance123"), role="coordinator")
            gensec = User(username="General Secretary", email_id="gensec.swifty@gmail.com", password=get_password_hash("admin123"), role="gensec")
            
            db.add_all([coordinator_music, gensec])
            db.commit()
            print("✅ Users seeded successfully.")

        # ==========================================
        # 2. SAFELY SEED CLUBS (Independent Check)
        # ==========================================
       # ==========================================
        # 2. SAFELY SEED OR UPDATE CLUBS
        # ==========================================
        if db.query(Club).first():
            print("⏭️  Clubs already exist. Checking for missing emails...")
            
            # Find the specific club we want to update
            music_club = db.query(Club).filter(Club.name == "Music Club").first()
            
            if music_club:
                # Update just the email field
                music_club.email = "gymkhana.swifty@gmail.com"
                db.commit()
                print("✅ Successfully updated the Music Club's email!")
            else:
                print("⚠️ Music Club not found in the database.")
                
        else:
            print("🏢 Restoring Clubs...")
            club_music = Club(name="Music Club", email="gymkhana.swifty@gmail.com", user_id=1, total_allocated=500000.0)
            
            db.add_all([club_music])
            db.commit()
            print("✅ Clubs seeded successfully.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()