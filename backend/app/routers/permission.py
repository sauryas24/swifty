from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, database, schemas
from ..utils import security

router = APIRouter(
    prefix="/api/permission",
    tags=["Permission Letter"]
)

# ============================================================
# ENDPOINT 1: Submit a new Permission Letter
# ============================================================
@router.post("/submit", response_model=schemas.PermissionLetterResponse)
def submit_permission_letter(
    letter: schemas.PermissionLetterCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user) 
):
    """
    Takes form data from the frontend and creates a new permission letter.
    """
    # Security check: Ensure only club coordinators can submit requests
    if current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Only coordinators can submit permission letters.")

    # Create the letter and start the approval chain
    new_letter = models.PermissionLetter(
        event_name=letter.event_name,
        date=letter.date,
        time=letter.time,
        reason=letter.reason,
        club_id=current_user.id,   # Automatically link it to the logged-in user
        status="Pending GenSec"    # Hands it off to your approvals pipeline!
    )

    db.add(new_letter)
    db.commit()
    db.refresh(new_letter)

    return new_letter



# ============================================================
# ENDPOINT 2: Get a single permission letter by ID
# ============================================================
@router.get("/{letter_id}", response_model=schemas.PermissionLetterResponse)
def get_single_letter(letter_id: int, db: Session = Depends(database.get_db)):
    """
    Used by the frontend to view the full details of a specific letter 
    (e.g., when an authority clicks "View Details" to decide to approve or reject).
    """
    letter = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.id == letter_id
    ).first()

    if not letter:
        raise HTTPException(status_code=404, detail="Permission letter not found")

    return letter