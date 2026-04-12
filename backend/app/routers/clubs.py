from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas

router = APIRouter(prefix="/api/clubs", tags=["Clubs"])

@router.get("/", response_model=List[schemas.ClubResponse])
def get_all_clubs(db: Session = Depends(database.get_db)):
    # Fetches all clubs from the database and uses ClubResponse to safely format as JSON
    clubs = db.query(models.Club).all()
    return clubs