import sys
import os
import pytest
from fastapi.testclient import TestClient

# Tell Python to look in the parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import SessionLocal
from app.models import User, PermissionLetter, VenueBooking, Club
from app.utils.security import get_current_user
from tests.seed_db import master_seed

client = TestClient(app)

# ==========================================
# SETUP: THE MAGIC FIXTURE
# ==========================================
@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    """
    This fixture runs exactly ONCE before the entire test suite starts.
    It completely wipes and rebuilds the database using your master seed script!
    """
    master_seed()


# ==========================================
# MOCK USERS FOR SECURITY BYPASS
# ==========================================
# We use these to bypass the OTP email system during automated testing
mock_coordinator = User(id=1, username="Music Club", role="coordinator", email_id="music@iitk.ac.in")
mock_gensec = User(id=2, username="GenSec", role="gensec", email_id="gensec@iitk.ac.in")
mock_president = User(id=3, username="President", role="president", email_id="president@iitk.ac.in")

def override_auth(mock_user):
    """Helper to force the API to act as a specific user."""
    app.dependency_overrides[get_current_user] = lambda: mock_user


# ==========================================
# 1. FINANCE TESTS
# ==========================================
def test_finance_dashboard_and_transaction():
    override_auth(mock_coordinator)
    
    # 1. Check initial budget (Should be 500k allocated, 19500 spent from seed)
    res_status = client.get("/api/finances/status")
    assert res_status.status_code == 200
    assert res_status.json()["total_spent"] == 19500.0
    
    # 2. Submit a new bill for ₹500
    res_tx = client.post(
        "/api/finances/transactions",
        json={"amount": 500.0, "description": "Pizza for club meeting"}
    )
    assert res_tx.status_code == 200
    
    # 3. Verify the dashboard updated the math!
    res_updated = client.get("/api/finances/status")
    assert res_updated.json()["total_spent"] == 20000.0


# ==========================================
# 2. SECURITY TESTS
# ==========================================
def test_unauthorized_approval_fails():
    # A coordinator tries to approve a venue booking (Hacking attempt!)
    override_auth(mock_coordinator)
    
    db = SessionLocal()
    pending_venue = db.query(VenueBooking).filter(VenueBooking.status == "Pending GenSec").first()
    db.close()
    
    response = client.put(
        f"/api/approvals/venue/{pending_venue.id}/process",
        json={"action": "approve", "message": "I approve my own event!"}
    )
    
    # The API MUST throw a 403 Forbidden error
    assert response.status_code == 403


# ==========================================
# 3. APPROVAL PIPELINE TESTS
# ==========================================
def test_permission_letter_approval_chain():
    db = SessionLocal()
    # Find the letter waiting for GenSec
    letter = db.query(PermissionLetter).filter(PermissionLetter.status == "Pending GenSec").first()
    letter_id = letter.id
    db.close()
    
    # 1. GenSec Approves
    override_auth(mock_gensec)
    res_1 = client.put(
        f"/api/approvals/permission/{letter_id}/process",
        json={"action": "approve", "message": "Looks good."}
    )
    assert res_1.status_code == 200
    assert "Pending President" in res_1.json()["message"]
    
    # 2. President Approves
    override_auth(mock_president)
    res_2 = client.put(
        f"/api/approvals/permission/{letter_id}/process",
        json={"action": "approve", "message": "Approved by Pres."}
    )
    assert res_2.status_code == 200
    assert "Pending FacAd" in res_2.json()["message"]


# ==========================================
# 4. CALENDAR TESTS
# ==========================================
def test_public_calendar_shows_approved_events():
    # Clear overrides so it acts like a normal public user
    app.dependency_overrides.clear() 
    
    response = client.get("/api/calendar/events")
    assert response.status_code == 200
    
    events = response.json()
    event_titles = [e["event_title"] for e in events]
    
    # From our seed data, "Sports Trials" was Approved, so it MUST be here
    assert "Sports Trials" in event_titles
    # "Secret Club Meeting" was Pending, so it MUST NOT be here
    assert "Secret Club Meeting" not in event_titles