from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, database, schemas
from ..utils import security

router = APIRouter(
    prefix="/api/permission",
    tags=["Permission Letter"]
)

# Endpoint 1: Submitting a new Permission Letter

# Receives event details from the frontend and creates a new permission request to start the approval pipeline.
@router.post("/submit", response_model=schemas.PermissionLetterResponse)
def submit_permission_letter(
    letter: schemas.PermissionLetterCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user) 
):
    # Verify the user has the 'coordinator' role before allowing submission.
    if current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Only coordinators can submit permission letters.")

    # Create the letter object and set its status to the beginning of the administrative pipeline.
    new_letter = models.PermissionLetter(
        event_name=letter.event_name,
        date=letter.date,
        time=letter.time,
        reason=letter.reason,
        club_id=current_user.id,   
        status="Pending GenSec"    
    )

    db.add(new_letter)
    db.commit()
    db.refresh(new_letter)

    return new_letter



# Endpoint 2: Get a single permission letter by ID

# Retrieves the full contents of a specific permission letter, generally used when an authority is reviewing it.
@router.get("/{letter_id}", response_model=schemas.PermissionLetterResponse)
def get_single_letter(letter_id: int, db: Session = Depends(database.get_db)):
    
    # Query the database for the exact letter ID provided.
    letter = db.query(models.PermissionLetter).filter(
        models.PermissionLetter.id == letter_id
    ).first()

    if not letter:
        raise HTTPException(status_code=404, detail="Permission letter not found")

    return letter