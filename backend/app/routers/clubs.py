from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas

router = APIRouter(prefix="/api/clubs", tags=["Clubs"])

@router.get("/", response_model=List[schemas.ClubResponse])
def get_all_clubs(db: Session = Depends(database.get_db)):
    return db.query(models.Club).all()