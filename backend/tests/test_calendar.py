import pytest
from fastapi.testclient import TestClient

# Import your FastAPI app and real database dependencies
from app.main import app
from app.database import SessionLocal, engine
from app.models import Base, Room, VenueBooking
from app.routers.calendar import approve_and_publish_event

# Create the test client (no dependency overrides needed since we WANT the real DB)
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # 1. Connect to the real swifty.db and ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 2. Check if the mock room already exists to prevent IntegrityErrors
    room = db.query(Room).filter(Room.name == "Main Stadium").first()
    if not room:
        room = Room(name="Main Stadium", capacity=1000)
        db.add(room)
        db.commit()
        db.refresh(room)
    
    # 3. Check if the PENDING booking already exists
    pending_event = db.query(VenueBooking).filter(VenueBooking.event_title == "Secret Club Meeting").first()
    if not pending_event:
        pending_event = VenueBooking(
            date="2026-04-10", 
            time="10:00 AM", 
            room_id=room.id,
            event_title="Secret Club Meeting", 
            event_type="Meeting",
            status="Pending FacAd" # Starts the approval chain
        )
        db.add(pending_event)
    
    # 4. Check if the APPROVED booking already exists
    approved_event = db.query(VenueBooking).filter(VenueBooking.event_title == "Sports Trials").first()
    if not approved_event:
        approved_event = VenueBooking(
            date="2026-04-15", 
            time="06:30 AM", 
            room_id=room.id,
            event_title="Sports Trials", 
            event_type="Athletics",
            status="Approved"
        )
        db.add(approved_event)
    
    db.commit()
    
    yield db  # Hand the database over to the test function
    
    # Notice we REMOVED the drop_all() command here! 
    # This means the data will stay safely in your swifty.db.
    db.close()


# --- The Actual Tests ---

def test_get_public_calendar_events(test_db):
    """
    Test that the calendar endpoint returns 'Approved' events from swifty.db.
    """
    response = client.get("/calendar/events")
    assert response.status_code == 200
    
    data = response.json()
    
    # Since swifty.db keeps its data, we check if our event is IN the list 
    # instead of checking if it's the ONLY item in the list.
    event_titles = [event["event_title"] for event in data]
    assert "Sports Trials" in event_titles
    
def test_approve_and_publish_event_function(test_db):
    """
    Test the utility function that changes a pending event to approved.
    """
    # Fetch the specific pending event we created so we have its exact dynamic ID
    pending_booking = test_db.query(VenueBooking).filter(
        VenueBooking.event_title == "Secret Club Meeting"
    ).first()
    
    # Call the function