import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

# Adjust these imports based on your actual project structure
from app.main import app
from app.database import get_db, Base
from app.models import User, Announcement
from app.utils.security import get_current_user

# 1. Setup isolated test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_swifty.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Override database dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 3. Fixtures for database setup and client
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Mock Users ---
def mock_authority_user():
    return User(id=1, username="General Secretary", email_id="gensec@iitk.ac.in", role="authority")

def mock_coordinator_user():
    return User(id=2, username="Music Club", email_id="music@iitk.ac.in", role="coordinator")

def mock_another_coordinator():
    return User(id=3, username="Dance Club", email_id="dance@iitk.ac.in", role="coordinator")

# --- Setup initial users in DB for email testing ---
@pytest.fixture(autouse=True)
def populate_users(db_session):
    if db_session.query(User).count() == 0:
        db_session.add_all([mock_authority_user(), mock_coordinator_user(), mock_another_coordinator()])
        db_session.commit()

# --- Test Cases ---

@patch("app.utils.email_service.send_notification_email")
def test_publish_announcement_as_authority(mock_send_email, client, db_session):
    app.dependency_overrides[get_current_user] = mock_authority_user
    
    payload = {
        "heading": "Auditorium Maintenance",
        "message": "The main auditorium will be closed.",
        "target_clubs": ["Music Club"]
    }
    
    response = client.post("/api/announcements/publish", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["heading"] == payload["heading"]
    assert data["sender_username"] == "General Secretary"
    
    # Verify DB insertion
    db_announcement = db_session.query(Announcement).filter_by(id=data["id"]).first()
    assert db_announcement is not None
    
    # Verify the mocked email service was called
    mock_send_email.assert_called()

def test_publish_announcement_as_coordinator(client):
    app.dependency_overrides[get_current_user] = mock_coordinator_user
    
    payload = {
        "heading": "Rogue Post",
        "message": "Coordinators shouldn't do this."
    }
    
    response = client.post("/api/announcements/publish", json=payload)
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Only administrative authorities can publish announcements."

def test_get_my_announcements_as_coordinator(client):
    app.dependency_overrides[get_current_user] = mock_coordinator_user
    
    response = client.get("/api/announcements/my-announcements")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # The Music Club should see the announcement we created in the first test
    assert len(data) >= 1
    assert data[0]["heading"] == "Auditorium Maintenance"

def test_get_my_announcements_as_authority(client):
    app.dependency_overrides[get_current_user] = mock_authority_user
    
    response = client.get("/api/announcements/my-announcements")
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Only club coordinators can view announcements."

# Clean up
def teardown_module(module):
    app.dependency_overrides.clear()