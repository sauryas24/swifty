from app.database import SessionLocal
from app.models import PermissionLetter, User

def seed_permission_letters():
    db = SessionLocal()
    #Make sure users exist first
    # Run seed_users.py before this file!
    users = db.query(User).filter(User.role == "coordinator").all()
    if not users:
        print("❌ Error: No coordinator users found in the database.")
        print("Please run 'python -m tests.seed_users' first.")
        db.close()
        return

    # Use the first coordinator found
    coordinator = users[0]

    # Avoid adding duplicates
    if db.query(PermissionLetter).count() > 0:
        print("Permission letters already exist. Skipping.")
        db.close()
        return

    print("Adding sample permission letters to the database...")

    letters_to_add = [
        # 1. Waiting for GenSec approval (first step in chain)
        PermissionLetter(
            event_name="Annual Music Showcase",
            date="2026-04-10",
            time="18:00",
            reason="End of semester cultural performance by the Music Club. Expected audience of 200 students.",
            club_id=coordinator.id,
            status="Pending GenSec"
        ),

        # 2. Waiting for FacAd approval (GenSec already approved)
        PermissionLetter(
            event_name="Workshop on Music Production",
            date="2026-04-15",
            time="14:00",
            reason="Hands-on workshop on digital music production tools for club members.",
            club_id=coordinator.id,
            status="Pending FacAd"
        ),

        # 3. Waiting for ADSA approval (GenSec + FacAd approved)
        PermissionLetter(
            event_name="Inter-College Jam Session",
            date="2026-04-20",
            time="16:00",
            reason="Collaborative music event inviting performers from nearby colleges.",
            club_id=coordinator.id,
            status="Pending ADSA"
        ),

        # 4. Fully approved — shows up on public calendar
        PermissionLetter(
            event_name="Acoustic Night",
            date="2026-03-25",
            time="19:00",
            reason="Unplugged performances by club members in an informal setting.",
            club_id=coordinator.id,
            status="Approved"
        ),

        # 5. Rejected — coordinator can see the reason
        PermissionLetter(
            event_name="Midnight Concert",
            date="2026-03-30",
            time="23:00",
            reason="Late night music concert on campus grounds.",
            club_id=coordinator.id,
            status="Rejected",
            comments="Events cannot be held after 10 PM as per institute policy."
        ),

        # ============================================================
        # ADD YOUR OWN ENTRIES BELOW THIS LINE
        # Just copy one of the blocks above and change the values!
        # ============================================================

        # Example template (uncomment and fill in):
        # PermissionLetter(
        #     event_name="Your Event Name",
        #     date="2026-05-01",         # YYYY-MM-DD format
        #     time="15:00",              # HH:MM format
        #     reason="Your reason here",
        #     club_id=coordinator.id,
        #     status="Pending GenSec"    # Starting status
        # ),
    ]

    db.add_all(letters_to_add)
    db.commit()
    print(f"✅ Success! {len(letters_to_add)} permission letters added.")
    db.close()


if __name__ == "__main__":
    seed_permission_letters()