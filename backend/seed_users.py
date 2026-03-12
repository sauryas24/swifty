from app.database import SessionLocal
from app.models import User
from app.utils.security import get_password_hash

def seed_users():
    db = SessionLocal()
    
    if db.query(User).count() == 0:
        print("Adding sample users to the database...")
        
        users_to_add = [
            # Sample Club Coordinator
            User(
                username="Music Club",
                email_id="m",
                password=get_password_hash("music123"), # Scrambles the password!
                role="coordinator"
            ),
            # Sample Authority
            User(
                username="General Secretary",
                email_id="gensec@iitk.ac.in",
                password=get_password_hash("admin123"),
                role="authority"
            )
        ]
        
        db.add_all(users_to_add)
        db.commit()
        print("Success! Sample users added.")
    else:
        print("Users already exist. Skipping.")
        
    db.close()

if __name__ == "__main__":
    seed_users()