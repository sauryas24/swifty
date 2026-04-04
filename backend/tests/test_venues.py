import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

# Import the functions and models
from app.routers.venues import get_time_variants, check_availability, submit_venue_booking
from app import models

# ==========================================
# UNIT TESTS: get_time_variants()
# ==========================================

def test_get_time_variants_mapping():
    """Prove the helper function correctly returns database formats."""
    # Test a known mapping
    variants = get_time_variants("02:00 PM - 04:00 PM")
    assert "14:00-16:00" in variants
    assert "14:00 - 16:00" in variants
    assert "02:00 PM - 04:00 PM" in variants

    # Test an unknown/fallback string
    assert get_time_variants("Midnight") == ["Midnight"]

# ==========================================
# UNIT TESTS: check_availability()
# ==========================================

def test_check_availability_logic():
    """Prove that rooms are correctly sorted into available and unavailable."""
    # 1. Arrange
    mock_db = MagicMock()
    room_1 = MagicMock(id=1, name="L1")
    room_2 = MagicMock(id=2, name="L2")
    conflict_booking = MagicMock(room_id=1) # Room 1 is booked!

    # Create a smart mock that answers differently based on the table queried
    def mock_db_query(model):
        mock_query = MagicMock()
        if model == models.Room:
            mock_query.all.return_value = [room_1, room_2]
        elif model == models.VenueBooking:
            mock_query.filter.return_value.all.return_value = [conflict_booking]
        return mock_query
    
    mock_db.query.side_effect = mock_db_query

    # 2. Act
    result = check_availability(date="2026-10-15", time="09:00 AM - 11:00 AM", db=mock_db)

    # 3. Assert
    assert room_1 in result["unavailable_rooms"]
    assert room_2 in result["available_rooms"]

# ==========================================
# UNIT TESTS: submit_venue_booking() (Security & Errors)
# ==========================================

def test_submit_venue_blocks_non_coordinator():
    with pytest.raises(HTTPException) as exc_info:
        submit_venue_booking(booking_data=MagicMock(), db=MagicMock(), current_user=MagicMock(role="president"))
    assert exc_info.value.status_code == 403
    assert "Only Club Coordinators" in exc_info.value.detail

def test_submit_venue_invalid_permission_letter():
    mock_db = MagicMock()
    # Simulate DB finding no permission letter
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        submit_venue_booking(booking_data=MagicMock(), db=mock_db, current_user=MagicMock(role="coordinator"))
    assert exc_info.value.status_code == 404

def test_submit_venue_wrong_club():
    mock_db = MagicMock()
    # Simulate finding a letter, but it belongs to club #99
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(club_id=99)
    
    with pytest.raises(HTTPException) as exc_info:
        # The user trying to book is club #1
        submit_venue_booking(booking_data=MagicMock(), db=mock_db, current_user=MagicMock(id=1, role="coordinator"))
    assert exc_info.value.status_code == 403
    assert "another club's permission letter" in exc_info.value.detail

def test_submit_venue_unapproved_permission():
    mock_db = MagicMock()
    # Letter belongs to the right club, but isn't approved yet
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(club_id=1, status="Pending GenSec")
    
    with pytest.raises(HTTPException) as exc_info:
        submit_venue_booking(booking_data=MagicMock(), db=mock_db, current_user=MagicMock(id=1, role="coordinator"))
    assert exc_info.value.status_code == 400
    assert "not been fully approved yet" in exc_info.value.detail

def test_submit_venue_double_booking_conflict():
    mock_db = MagicMock()
    valid_perm = MagicMock(club_id=1, status="Approved")
    existing_conflict = MagicMock(id=5) # Someone else just booked it!

    def mock_db_query(model):
        mock_query = MagicMock()
        if model == models.PermissionLetter:
            mock_query.filter.return_value.first.return_value = valid_perm
        elif model == models.VenueBooking:
            mock_query.filter.return_value.first.return_value = existing_conflict
        return mock_query
    
    mock_db.query.side_effect = mock_db_query

    with pytest.raises(HTTPException) as exc_info:
        submit_venue_booking(booking_data=MagicMock(), db=mock_db, current_user=MagicMock(id=1, role="coordinator"))
    assert exc_info.value.status_code == 409
    assert "has just been booked" in exc_info.value.detail

# ==========================================
# UNIT TESTS: submit_venue_booking() (Success)
# ==========================================

def test_submit_venue_success():
    mock_db = MagicMock()
    valid_perm = MagicMock(club_id=1, status="Approved")

    def mock_db_query(model):
        mock_query = MagicMock()
        if model == models.PermissionLetter:
            mock_query.filter.return_value.first.return_value = valid_perm
        elif model == models.VenueBooking:
            mock_query.filter.return_value.first.return_value = None # No conflicts!
        return mock_query
    
    mock_db.query.side_effect = mock_db_query
    
    # Fake the incoming JSON data
    mock_data = MagicMock(date="2026-10-15", time="09:00 AM - 11:00 AM", room_id=2, event_title="Tech Demo")
    
    # Act
    result = submit_venue_booking(booking_data=mock_data, db=mock_db, current_user=MagicMock(id=1, role="coordinator"))
    
    # Assert
    assert mock_db.add.called
    assert mock_db.commit.called
    assert result["message"] == "Booking request submitted successfully!"
    assert result["status"] == "Pending GenSec"