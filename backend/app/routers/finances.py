from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from .. import models, schemas, database
import shutil
import os

router = APIRouter(prefix="/finances", tags=["finances"])

@router.get("/{club_id}", response_model=schemas.ClubFinanceStatus)
def get_club_finances(club_id: int, db: Session = Depends(database.get_db)):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Calculate derived values for the UI progress bar
    remaining = club.total_allocated - club.total_spent
    utilization = (club.total_spent / club.total_allocated) * 100 if club.total_allocated > 0 else 0
    
    return {
        "name": club.name,
        "total_allocated": club.total_allocated,
        "total_spent": club.total_spent,
        "remaining_balance": remaining,
        "utilization_percentage": utilization,
        "transactions": club.transactions
    }

@router.post("/upload-bill")
async def upload_bill(
    club_id: int = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    # 1. Save the file to the static directory as shown in SDD requirements [cite: 1947, 1967]
    file_location = f"static/receipts/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    # 2. Update the Club's budget status [cite: 1948, 2035]
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    club.total_spent += amount
    
    # 3. Create a persistent transaction log [cite: 1950, 2036]
    new_transaction = models.Transaction(
        club_id=club_id,
        amount=amount,
        description=description,
        receipt_url=file_location
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return {"message": "Bill uploaded and budget updated successfully"}