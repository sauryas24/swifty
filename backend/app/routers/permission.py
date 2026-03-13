from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models
from ..database import get_db
from ..schemas import PermissionLetterCreate, PermissionLetterResponse

router = APIRouter(
    prefix="/permission",
    tags=["Permission Letter"]
)

# ============================================================
# THE APPROVAL CHAIN
# Matches exactly your sequence diagram (3.3.3):
#   Coordinator → GenSec → FacAd → ADSA (Dean) → Approved
#
# APPROVAL_CHAIN maps: current status → next status after approval
# ROLE_TO_STATUS maps: who logs in → what status they can act on
# ============================================================

APPROVAL_CHAIN = {
    "Pending GenSec": "Pending FacAd",
    "Pending FacAd":  "Pending ADSA",
    "Pending ADSA":   "Approved"
}

ROLE_TO_STATUS = {
    "GenSec": "Pending GenSec",
    "FacAd":  "Pending FacAd",
    "ADSA":   "Pending ADSA"
}


# ============================================================
# ENDPOINT 1: Submit a new Permission Letter
# Called when coordinator clicks "Submit Request" on the form
# ============================================================

@router.post("/submit", response_model=PermissionLetterResponse)
def submit_permission_letter(
    letter: PermissionLetterCreate,
    db: Session = Depends(get_db),
    club_id: int = None   # In future, extract this from JWT token
):
    """
    What the frontend sends (matches your form fields):
    {
        "event_name": "Annual Music Showcase",
        "date": "2026-04-01",
        "time": "18:00",
        "reason": "End of semester performance..."
    }

    What this does:
    1. Takes the form data from the frontend
    2. Saves it to the permission_letters table in the DB
    3. Sets status to "Pending GenSec" automatically (first in chain)
    4. Returns the new letter's ID and status to the frontend

    NOTE: council_name and club_name are NOT stored separately —
    they come from the logged-in User's associate_council and username.
    That's why the form has them as locked/read-only fields.
    """

    # Create a new PermissionLetter row in the DB
    # Matching exactly your PermissionLetter model in models.py
    new_letter = models.PermissionLetter(
        event_name=letter.event_name,
        date=letter.date,
        time=letter.time,
        reason=letter.reason,
        club_id=club_id,           # Links to the coordinator's user ID
        status="Pending GenSec"    # Always starts at GenSec — first in chain
    )

    db.add(new_letter)
    db.commit()
    db.refresh(new_letter)   # Refresh to get the auto-generated ID back

    return new_letter        # Returns id, event_name, status (matches PermissionLetterResponse)


# ============================================================
# ENDPOINT 2: Get all permission letters for a club
# Called by Past Requests page to show the coordinator
# their submission history with statuses
# ============================================================

@router.get("/club/{club_id}", response_model=List[PermissionLetterResponse])
def get_letters_for_club(club_id: int, db: Session = Depends(get_db)):
    """
    Returns all permission letters submitted by this club.
    Ordered newest first.

    Frontend calls:
        GET /permission/club/3
    """
    letters = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.club_id == club_id
    ).order_by(models.PermissionLetter.id.desc()).all()

    return letters


# ============================================================
# ENDPOINT 3: Get a single permission letter by ID
# Called when someone clicks "View Details"
# ============================================================

@router.get("/{letter_id}", response_model=PermissionLetterResponse)
def get_single_letter(letter_id: int, db: Session = Depends(get_db)):
    """
    Frontend calls:
        GET /permission/5
    """
    letter = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.id == letter_id
    ).first()

    if not letter:
        raise HTTPException(status_code=404, detail="Permission letter not found")

    return letter


# ============================================================
# ENDPOINT 4: Authority approves or rejects a permission letter
# Called from the AUTHORITY dashboard
#
# Approval flow:
#   GenSec approves → status becomes "Pending FacAd"
#   FacAd approves  → status becomes "Pending ADSA"
#   ADSA approves   → status becomes "Approved" ✅
#   Anyone rejects  → status becomes "Rejected" ❌ (chain stops)
# ============================================================

@router.put("/{letter_id}/action")
def take_action_on_letter(
    letter_id: int,
    action: str,               # "approve" or "reject"
    authority_role: str,       # "GenSec", "FacAd", or "ADSA"
    comment: str = None,       # Required only when rejecting
    db: Session = Depends(get_db)
):
    """
    Called from the authority's dashboard.

    To APPROVE:
        PUT /permission/5/action?action=approve&authority_role=GenSec

    To REJECT (comment is required):
        PUT /permission/5/action?action=reject&authority_role=GenSec&comment=Missing+details

    Safety checks:
    - FacAd cannot approve something still waiting for GenSec
    - Rejection always requires a comment (your design doc says this)
    - Already approved/rejected letters cannot be acted on again
    """

    # 1. Get the letter from DB
    letter = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.id == letter_id
    ).first()

    if not letter:
        raise HTTPException(status_code=404, detail="Permission letter not found")

    # 2. Validate action value
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    # 3. Check the letter isn't already finished
    if letter.status in ["Approved", "Rejected"]:
        raise HTTPException(
            status_code=400,
            detail=f"This letter is already '{letter.status}' and cannot be changed"
        )

    # 4. Check this authority is allowed to act RIGHT NOW
    #    e.g. FacAd cannot approve if it's still "Pending GenSec"
    expected_status = ROLE_TO_STATUS.get(authority_role)
    if not expected_status:
        raise HTTPException(status_code=403, detail=f"Unknown authority role: {authority_role}")

    if letter.status != expected_status:
        raise HTTPException(
            status_code=403,
            detail=f"Not your turn. Letter is currently '{letter.status}', you handle '{expected_status}'"
        )

    # 5a. REJECTION — chain stops, comment saved to status field
    if action == "reject":
        if not comment:
            raise HTTPException(
                status_code=400,
                detail="You must provide a reason when rejecting"
            )
        # We store rejection info in the status field since model has no comment column
        # Format: "Rejected: <reason>" so frontend can split and display it
        letter.status = f"Rejected: {comment}"
        db.commit()
        return {
            "message": f"Rejected by {authority_role}",
            "status": letter.status
        }

    # 5b. APPROVAL — move to next step in chain
    next_status = APPROVAL_CHAIN.get(letter.status)
    letter.status = next_status
    db.commit()

    return {
        "message": f"Approved by {authority_role}. Now '{next_status}'",
        "status": next_status
    }


# ============================================================
# ENDPOINT 5: Get all letters pending for a specific authority
# Called when GenSec / FacAd / ADSA logs into their dashboard
# to see what needs their attention
# ============================================================

@router.get("/pending/{authority_role}", response_model=List[PermissionLetterResponse])
def get_pending_letters(authority_role: str, db: Session = Depends(get_db)):
    """
    Frontend calls:
        GET /permission/pending/GenSec    ← shows letters waiting for GenSec
        GET /permission/pending/FacAd     ← shows letters waiting for FacAd
        GET /permission/pending/ADSA      ← shows letters waiting for ADSA
    """
    required_status = ROLE_TO_STATUS.get(authority_role)
    if not required_status:
        raise HTTPException(status_code=400, detail=f"Unknown role: {authority_role}")

    pending = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.status == required_status
    ).all()

    return pending