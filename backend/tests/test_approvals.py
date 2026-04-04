import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Import the functions and schemas
from app.routers.approvals import _verify_otp, process_permission_approval, process_venue_approval
from app import schemas, models

# ==========================================
# UNIT TESTS: _verify_otp()
# ==========================================

def test_verify_otp_missing_code():
    """Prove that an empty OTP throws a 400 error."""
    with pytest.raises(HTTPException) as exc_info:
        _verify_otp("test@iitk.ac.in", "", MagicMock())
    assert exc_info.value.status_code == 400

def test_verify_otp_invalid_code():
    """Prove that a mismatched OTP throws a 400 error."""
    mock_db = MagicMock()
    mock_record = MagicMock(otp_code="123456")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_record

    with pytest.raises(HTTPException) as exc_info:
        _verify_otp("test@iitk.ac.in", "999999", mock_db)
    assert exc_info.value.status_code == 400

def test_verify_otp_expired():
    """Prove that an expired OTP is rejected and deleted from the database."""
    mock_db = MagicMock()
    # Set expiration to the year 2000 (definitely expired!)
    mock_record = MagicMock(otp_code="123456", expires_at="2000-01-01T00:00:00")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_record

    with pytest.raises(HTTPException) as exc_info:
        _verify_otp("test@iitk.ac.in", "123456", mock_db)
    
    assert exc_info.value.status_code == 400
    assert "OTP has expired" in exc_info.value.detail
    assert mock_db.delete.called # Ensure it cleans up the dead OTP!

def test_verify_otp_success():
    """Prove that a valid, unexpired OTP passes and is consumed."""
    mock_db = MagicMock()
    # Set expiration to the year 2099 (definitely valid!)
    mock_record = MagicMock(otp_code="123456", expires_at="2099-01-01T00:00:00")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_record

    # This should run without throwing an exception
    _verify_otp("test@iitk.ac.in", "123456", mock_db)
    
    # Ensure it consumes (deletes) the OTP after a single use
    assert mock_db.delete.called
    assert mock_db.commit.called

# ==========================================
# UNIT TESTS: process_permission_approval()
# ==========================================

@patch("app.routers.approvals.email_service.send_notification_email")
def test_permission_reject_flow(mock_email_service):
    """Prove that rejecting a request updates status and emails the user."""
    mock_db = MagicMock()
    mock_letter = MagicMock(status="Pending GenSec", event_name="Hackathon")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_letter
    
    # Simulated GenSec User
    current_user = MagicMock(role="gensec", email_id="gensec@iitk.ac.in")
    action_data = schemas.ApprovalAction(action="reject", message="Budget too high", otp_code="")

    result = process_permission_approval(letter_id=1, action_data=action_data, db=mock_db, current_user=current_user)

    assert result["message"] == "Permission letter rejected successfully."
    assert mock_letter.status == "Rejected by gensec"
    assert mock_letter.comments == "Budget too high"
    assert mock_email_service.called

@patch("app.routers.approvals._verify_otp") # Bypass actual OTP logic for this test
@patch("app.routers.approvals.email_service.send_notification_email")
def test_permission_final_approval_generates_id(mock_email_service, mock_verify_otp):
    """Prove that final ADSA approval generates the official PL-ID."""
    mock_db = MagicMock()
    mock_letter = MagicMock(status="Pending ADSA", event_name="Hackathon")
    
    # Make the DB count return '5' so the sequence generates '0006'
    def mock_db_query(model):
        mock_query = MagicMock()
        if model == models.PermissionLetter:
            # First call is getting the letter, second call is counting for the ID
            mock_query.filter.return_value.first.return_value = mock_letter
            mock_query.filter.return_value.count.return_value = 5 
        return mock_query
        
    mock_db.query.side_effect = mock_db_query
    
    # Simulated ADSA User
    current_user = MagicMock(role="adsa", email_id="adsa@iitk.ac.in")
    action_data = schemas.ApprovalAction(action="approve", otp_code="123456", message="")

    result = process_permission_approval(letter_id=1, action_data=action_data, db=mock_db, current_user=current_user)

    assert mock_letter.status == "Approved"
    # Verify the ID was generated dynamically based on the current year and count!
    assert "PL-" in mock_letter.generated_id
    assert mock_letter.generated_id.endswith("0006")
    assert result["generated_id"] == mock_letter.generated_id
    assert mock_email_service.called

# ==========================================
# UNIT TESTS: process_venue_approval()
# ==========================================

def test_venue_approval_unauthorized_role():
    """Prove that the President cannot approve something meant for the ADSA."""
    mock_db = MagicMock()
    # The request is at the end of the pipeline, waiting for ADSA
    mock_booking = MagicMock(status="Pending ADSA")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_booking
    
    # But a President tries to click approve!
    current_user = MagicMock(role="president")
    action_data = schemas.ApprovalAction(action="approve", otp_code="123456")

    with pytest.raises(HTTPException) as exc_info:
        process_venue_approval(booking_id=1, action_data=action_data, db=mock_db, current_user=current_user)
        
    assert exc_info.value.status_code == 403
    assert "Not authorized" in exc_info.value.detail