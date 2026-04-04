import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

# Import the functions directly from the router
from app.routers.permission import submit_permission_letter, get_single_letter

# ==========================================
# UNIT TESTS: submit_permission_letter()
# ==========================================

def test_submit_permission_blocks_non_coordinators():
    """Prove that an authority or standard student cannot submit a club request."""
    # 1. Arrange
    mock_db = MagicMock()
    mock_user = MagicMock(role="president") # Simulate an authority instead of a coordinator
    mock_letter_data = MagicMock()

    # 2. Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        submit_permission_letter(letter=mock_letter_data, db=mock_db, current_user=mock_user)
    
    assert exc_info.value.status_code == 403
    assert "Only coordinators can submit" in exc_info.value.detail

def test_submit_permission_success():
    """Prove that a coordinator can submit and the status defaults to GenSec."""
    # 1. Arrange
    mock_db = MagicMock()
    mock_user = MagicMock(id=5, role="coordinator")
    mock_letter_data = MagicMock(
        event_name="TechFest 2026", 
        date="2026-10-15", 
        time="18:00", 
        reason="Annual Tech Gathering"
    )

    # 2. Act
    result = submit_permission_letter(letter=mock_letter_data, db=mock_db, current_user=mock_user)

    # 3. Assert
    # Verify the database commit sequence was triggered
    assert mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.refresh.called
    
    # Verify the pipeline injection and data mapping worked
    assert result.event_name == "TechFest 2026"
    assert result.club_id == 5
    assert result.status == "Pending GenSec" # <--- Crucial pipeline test!

# ==========================================
# UNIT TESTS: get_single_letter()
# ==========================================

def test_get_single_letter_not_found():
    """Prove that querying a non-existent ID throws a 404 error."""
    # 1. Arrange
    mock_db = MagicMock()
    
    # Simulate the database finding absolutely nothing
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # 2. Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_single_letter(letter_id=999, db=mock_db)
        
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Permission letter not found"

def test_get_single_letter_success():
    """Prove that a valid ID returns the correct database object."""
    # 1. Arrange
    mock_db = MagicMock()
    
    # Simulate the database finding the correct letter
    mock_letter = MagicMock(id=42, event_name="Dance Workshop")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_letter

    # 2. Act
    result = get_single_letter(letter_id=42, db=mock_db)

    # 3. Assert
    assert result.id == 42
    assert result.event_name == "Dance Workshop"