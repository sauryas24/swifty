import sys
import os

# Tell Python to look in the parent folder for the 'app' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, User
from app.utils.security import get_password_hash

def restore_users():
    print("🔍 Checking database tables...")
    
    # create_all is safe: It ONLY creates tables that are missing.
    # It will NOT drop, overwrite, or touch your existing tables (like forms or ledgers).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Prevent accidental duplicates if the users are actually still there
        existing_user = db.query(User).first()
        if existing_user:
            print("⚠️ Users already exist in the database! Aborting to prevent duplicates.")
            return

        print("👤 Restoring Users...")
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

        db.add_all([
            coordinator_music, coordinator_dance, coordinator_drama, coordinator_prog, 
            gensec, president, facad, adsa
        ])
        
        db.commit()
        print("\n✅ SUCCESS! All users have been restored to the Neon database.")

    except Exception as e:
        print(f"\n❌ An error occurred while restoring users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore_users()