import pytest
from app.routers.requests import simplify_status, get_authority_pipeline_data

# ==========================================
# UNIT TESTS: simplify_status()
# ==========================================

def test_simplify_status_empty_handling():
    """Prove it defaults to Pending if no status is provided."""
    assert simplify_status(None) == "Pending"
    assert simplify_status("") == "Pending"

def test_simplify_status_approval_handling():
    """Prove it catches the word 'approved' regardless of casing."""
    assert simplify_status("Approved by DOSA") == "Approved"
    assert simplify_status("approved") == "Approved"
    assert simplify_status("HAS BEEN APPROVED") == "Approved"

def test_simplify_status_rejection_handling():
    """Prove it catches the word 'reject' regardless of casing."""
    assert simplify_status("Rejected by GenSec") == "Rejected"
    assert simplify_status("reject") == "Rejected"

def test_simplify_status_pending_passthrough():
    """Prove that specific Pending statuses pass through untouched."""
    assert simplify_status("Pending President") == "Pending President"
    assert simplify_status("Pending FacAd") == "Pending FacAd"


# ==========================================
# UNIT TESTS: get_authority_pipeline_data()
# ==========================================

def test_pipeline_data_for_president():
    """Test the pipeline logic specifically from the President's perspective."""
    
    # 1. Arrange: Extract the 3 returned variables for the 'president' role
    target_status, is_history, format_status = get_authority_pipeline_data("president")
    
    # 2. Assert: Check the Target Status
    assert target_status == "Pending President"
    
    # 3. Assert: Check is_history() logic
    # - True if it's currently beyond them in the pipeline
    assert is_history("Pending FacAd") is True
    assert is_history("Pending ADSA") is True
    assert is_history("Approved") is True
    
    # - False if it hasn't reached them yet
    assert is_history("Pending GenSec") is False
    
    # - True if they rejected it themselves
    assert is_history("Rejected by president") is True
    
    # - True if it was rejected AFTER they approved it (e.g., FacAd rejected it)
    assert is_history("Rejected by facad") is True
    
    # - False if it was rejected BEFORE it reached them (e.g., GenSec rejected it)
    assert is_history("Rejected by gensec") is False

def test_format_status_for_viewer_president():
    """Test that the UI gets the correct badge text from the President's perspective."""
    _, _, format_status = get_authority_pipeline_data("president")
    
    # If it's on their desk right now, it should say "Pending President"
    assert format_status("Pending President") == "Pending President"
    
    # If they rejected it, it should just say "Rejected"
    assert format_status("Rejected by president") == "Rejected"
    
    # If it is anywhere past them in the pipeline, it means *they* approved it!
    assert format_status("Pending FacAd") == "Approved"
    assert format_status("Approved") == "Approved"

def test_pipeline_data_invalid_role():
    """Prove the logic doesn't crash if a bad role is passed."""
    target_status, is_history, format_status = get_authority_pipeline_data("random_hacker")
    
    assert target_status is None
    assert is_history("Pending GenSec") is False
    assert format_status("Some Status") == "Some Status"