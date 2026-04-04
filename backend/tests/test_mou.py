import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

# Import the functions directly from the router
from app.routers.MoU import submit_mou, get_mou

# ==========================================
# UNIT TESTS: submit_mou()
# ==========================================

def test_submit_mou_blocks_non_coordinators():
    """Prove that an authority cannot submit an MoU request."""
    # 1. Arrange
    mock_db = MagicMock()
    mock_user = MagicMock(role="president") # An authority role
    mock_document = MagicMock()

    # 2. Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        submit_mou(
            organization_name="Tech Corp", 
            purpose="Sponsorship", 
            document=mock_document, 
            db=mock_db, 
            current_user=mock_user
        )
    
    assert exc_info.value.status_code == 403
    assert "Only coordinators can submit" in exc_info.value.detail

# Intercept the Cloudinary uploader so we don't upload real files during testing!
@patch('app.routers.MoU.cloudinary.uploader.upload')
def test_submit_mou_cloudinary_failure(mock_cloudinary_upload):
    """Prove that if Cloudinary crashes, the backend safely handles the error."""
    # 1. Arrange
    mock_db = MagicMock()
    mock_user = MagicMock(role="coordinator")
    
    # Simulate Cloudinary throwing a network error
    mock_cloudinary_upload.side_effect = Exception("Cloudinary servers are down")

    # 2. Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        submit_mou(
            organization_name="Tech Corp", 
            purpose="Sponsorship", 
            document=MagicMock(), 
            db=mock_db, 
            current_user=mock_user
        )
        
    assert exc_info.value.status_code == 500
    assert "Cloudinary upload failed: Cloudinary servers are down" in exc_info.value.detail

@patch('app.routers.MoU.cloudinary.uploader.upload')
def test_submit_mou_success(mock_cloudinary_upload):
    """Prove the happy path: Cloudinary succeeds, DB saves, Pipeline starts."""
    # 1. Arrange
    mock_db = MagicMock()
    mock_user = MagicMock(id=1, role="coordinator")
    mock_document = MagicMock()
    
    # Simulate a perfectly successful Cloudinary upload returning a secure URL
    mock_cloudinary_upload.return_value = {
        "secure_url": "https://res.cloudinary.com/demo/image/upload/sample.pdf"
    }

    # 2. Act
    result = submit_mou(
        organization_name="Tech Corp", 
        purpose="Sponsorship", 
        document=mock_document, 
        db=mock_db, 
        current_user=mock_user
    )

    # 3. Assert
    # Verify the third-party API was actually called
    assert mock_cloudinary_upload.called
    
    # Verify the database commit sequence
    assert mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.refresh.called
    
    # Verify the data was mapped correctly and pipeline status was set
    assert result.organization_name == "Tech Corp"
    assert result.document_url == "https://res.cloudinary.com/demo/image/upload/sample.pdf"
    assert result.status == "Pending GenSec"

# ==========================================
# UNIT TESTS: get_mou()
# ==========================================

def test_get_mou_not_found():
    """Prove that querying a non-existent ID throws a 404 error."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_mou(mou_id=999, db=mock_db, current_user=MagicMock())
        
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "MoU not found"

def test_get_mou_success():
    """Prove that a valid ID returns the correct database object."""
    mock_db = MagicMock()
    mock_mou = MagicMock(id=5, organization_name="Google")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_mou

    result = get_mou(mou_id=5, db=mock_db, current_user=MagicMock())

    assert result.id == 5
    assert result.organization_name == "Google"