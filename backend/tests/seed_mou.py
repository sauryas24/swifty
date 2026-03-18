from app.database import SessionLocal
from app.models import User, MoURequest

def seed_mous():
    # Open a connection to the database
    db = SessionLocal()
    
    # 1. Fetch a coordinator user (e.g., Music Club) to link the MoU to
    # We need a user ID because the MoU model requires a coordinator_id as a foreign key
    coordinator = db.query(User).filter(User.role == "coordinator").first()

    # Safety Check: We cannot make an MoU if there are no users!
    if not coordinator:
        print("❌ Error: No coordinator found in the database.")
        print("Please ensure you have users in your database first.")
        db.close()
        return

    # 2. Check if MoUs already exist to avoid spamming the database
    if db.query(MoURequest).count() == 0:
        print("Adding sample MoU requests to the database...")
        
        # Creating dummy MoUs based on the UI mockups in the Design Doc
        mous_to_add = [
            # An Approved MoU
            MoURequest(
                coordinator_id=coordinator.id,
                organization_name="Brand-X",
                purpose="Sponsorship with Brand-X",
                document_url="static/docs/dummy_brand_x_mou.pdf",
                status="Approved"
            ),
            # A Pending MoU
            MoURequest(
                coordinator_id=coordinator.id,
                organization_name="Media Coverage Partner",
                purpose="Media Coverage for upcoming fest",
                document_url="static/docs/dummy_media_mou.pdf",
                status="Pending Gensec" 
            ),
            # A Rejected MoU (To test your comment display popup!)
            MoURequest(
                coordinator_id=coordinator.id,
                organization_name="Local Sound Rentals",
                purpose="Annual Audio Equipment Supply",
                document_url="static/docs/dummy_audio_mou.pdf",
                status="Rejected",
                comments="Please revise the payment terms as per DOSA guidelines."
            )
        ]
        
        db.add_all(mous_to_add)
        db.commit()
        print(f"✅ Success! Sample MoU requests added for coordinator ID {coordinator.id}.")
    else:
        print("MoU requests already exist. Skipping.")
        
    db.close()

if __name__ == "__main__":
    seed_mous()