from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas

router = APIRouter(prefix="/api/clubs", tags=["Clubs"])

@router.get("", response_model=List[schemas.ClubResponse])
def get_all_clubs(db: Session = Depends(database.get_db)):
    clubs = db.query(models.Club).all()
    
    # Map the email from the connected user table
    result = []
    for club in clubs:
        result.append({
            "id": club.id,
            "name": club.name,
            "email": club.user.email_id if club.user else "" 
        })
    return result