import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

# Import the functions directly from the router
from app.routers.announcements import publish_announcement, get_announcements

# ==========================================
# UNIT TESTS: publish_announcement()
# ==========================================

def test_publish_announcement_blocks_coordinators():
    """Prove that a regular coordinator gets a 403 Forbidden error."""
    # 1. Arrange: Create fake inputs
    mock_db = MagicMock()
    mock_user = MagicMock(role="coordinator")
    mock_data = MagicMock(heading="Test", message="Test", target_clubs=[])

    # 2. Act & Assert: Check if it throws the 403 exception
    with pytest.raises(HTTPException) as exc_info:
        publish_announcement(announcement_data=mock_data, db=mock_db, current_user=mock_user)
    
    assert exc_info.value.status_code == 403
    assert "Only administrative authorities can publish" in exc_info.value.detail

# We use @patch to intercept the email service so we don't send real spam!
@patch("app.routers.announcements.email_service.send_notification_email")
def test_publish_announcement_sends_emails(mock_email_service):
    """Prove that authorized users can publish and emails trigger."""
    # 1. Arrange
    mock_db = MagicMock()
    mock_user = MagicMock(id=1, username="AdminUser", role="admin")
    mock_data = MagicMock(heading="Urgent", message="Read this", target_clubs=["Music Club"])
    
    # Setup the fake database response to pretend it found 1 target user
    mock_target_user = MagicMock(username="Music Club", email_id="music@iitk.ac.in")
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_target_user]

    # 2. Act
    result = publish_announcement(announcement_data=mock_data, db=mock_db, current_user=mock_user)

    # 3. Assert
    assert result["heading"] == "Urgent"
    assert result["target_clubs"] == ["Music Club"]
    
    # Verify the database commit was triggered
    assert mock_db.add.called
    assert mock_db.commit.called
    
    # Verify the email service was actually called with the exact formatting!
    mock_email_service.assert_called_once_with(
        to_email="music@iitk.ac.in",
        subject="New Announcement from AdminUser",
        body="Hello Music Club,\n\nYou have a new official announcement from AdminUser:\n\nRead this"
    )

# ==========================================
# UNIT TESTS: get_announcements()
# ==========================================

def test_get_announcements_visibility_rules():
    """Prove authorities see all, but clubs only see global + their own."""
    # 1. Arrange
    mock_db = MagicMock()
    
    # Create fake database rows simulating (Announcement, SenderUsername)
    global_ann = MagicMock(id=1, target_clubs="", heading="Global", message="For all")
    music_ann = MagicMock(id=2, target_clubs="Music Club", heading="Music Only", message="For music")
    dance_ann = MagicMock(id=3, target_clubs="Dance Club", heading="Dance Only", message="For dance")
    
    # Mock the chained .query().join().order_by().all() DB call
    mock_db.query.return_value.join.return_value.order_by.return_value.all.return_value = [
        (global_ann, "AdminUser"), 
        (music_ann, "AdminUser"), 
        (dance_ann, "AdminUser")
    ]

    # 2. Act 1: Authority User (Should see all 3 announcements)
    authority_user = MagicMock(role="admin")
    auth_results = get_announcements(db=mock_db, current_user=authority_user)
    assert len(auth_results) == 3

    # 3. Act 2: Music Club Coordinator (Should see 2: Global + Music)
    music_user = MagicMock(role="coordinator", username="Music Club")
    music_results = get_announcements(db=mock_db, current_user=music_user)
    assert len(music_results) == 2
    assert music_results[0]["heading"] == "Global"
    assert music_results[1]["heading"] == "Music Only"

    # 4. Act 3: Random User (Should see 1: Global Only)
    random_user = MagicMock(role="coordinator", username="Chess Club")
    random_results = get_announcements(db=mock_db, current_user=random_user)
    assert len(random_results) == 1
    assert random_results[0]["heading"] == "Global"