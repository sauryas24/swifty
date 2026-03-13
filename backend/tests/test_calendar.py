import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# We removed "backend." from the beginning of these 4 lines
from app.main import app
from app.database import get_db
from app.models import Base, Room, VenueBooking
from app.routers.calendar import approve_and_publish_event

# ... the rest of your test code stays exactly the same! ...
# 1. Setup the temporary "in-memory" SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Override the database dependency so the app uses our fake DB
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create the test client
client = TestClient(app)

# 3. Create a fixture to set up data before each test runs
@pytest.fixture(scope="function")
def test_db():
    # Create the tables in our temporary database
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Add a dummy room
    room = Room(name="Main Stadium", capacity=1000)
    db.add(room)
    db.commit()
    db.refresh(room)
    
    # Add one PENDING booking (should NOT show on calendar)
    pending_event = VenueBooking(
        date="2026-04-10", 
        time="10:00 AM", 
        room_id=room.id,
        event_title="Secret Club Meeting", 
        event_type="Meeting",
        status="Pending FacAd"
    )
    
    # Add one APPROVED booking (SHOULD show on calendar)
    approved_event = VenueBooking(
        date="2026-04-15", 
        time="06:30 AM", 
        room_id=room.id,
        event_title="Sports Trials", 
        event_type="Athletics",
        status="Approved"
    )
    
    db.add(pending_event)
    db.add(approved_event)
    db.commit()
    
    yield db  # This hands the database over to the test function
    
    # Clean up after the test is done
    Base.metadata.drop_all(bind=engine)

# --- The Actual Tests ---

def test_get_public_calendar_events(test_db):
    """
    Test that the calendar endpoint only returns 'Approved' events.
    """
    # Simulate a frontend GET request to the calendar endpoint
    response = client.get("/calendar/events")
    
    # Check that the request was successful (HTTP 200 OK)
    assert response.status_code == 200
    
    # Get the JSON data from the response
    data = response.json()
    
    # We added 2 events, but only 1 is approved. 
    # Therefore, the calendar should only return 1 event.
    assert len(data) == 1
    
    # Check that the returned event is indeed the approved one
    assert data[0]["event_title"] == "Sports Trials"
    assert data[0]["venue_name"] == "Main Stadium"
    
def test_approve_and_publish_event_function(test_db):
    """
    Test the utility function that changes a pending event to approved.
    """
    # In our test_db fixture, the pending event is the first one added, so it has ID 1
    pending_booking_id = 1 
    
    # Call the function we wrote earlier
    updated_booking = approve_and_publish_event(pending_booking_id, test_db)
    
    # Verify the status successfully changed
    assert updated_booking.status == "Approved"