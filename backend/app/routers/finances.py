import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..utils import security

router = APIRouter(prefix="/api/finances", tags=["finances"])

# 1. GET STATUS (Required for Dashboard & Tests)
@router.get("/status", response_model=schemas.ClubFinanceStatus)
def get_my_club_finances(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Security: Only fetch the club belonging to the logged-in user
    # Inside get_my_club_finances and submit_json_transaction
    # Use this query in your GET and POST routes in finances.py
    club = db.query(models.Club).filter(
    (models.Club.user_id == current_user.id) | (models.Club.name == current_user.username)
).first()
    if not club:
        raise HTTPException(status_code=404, detail="Finance ledger not found.")
    
    remaining = club.total_allocated - club.total_spent
    utilization = (club.total_spent / club.total_allocated) * 100 if club.total_allocated > 0 else 0
    
    return {
        "name": club.name,
        "total_allocated": club.total_allocated,
        "total_spent": club.total_spent,
        "remaining_balance": remaining,
        "utilization_percentage": round(utilization, 2),
        "transactions": club.transactions
    }

# 4. GET SPECIFIC CLUB STATUS (For ADSA/DOSA Dashboard)
@router.get("/{club_id}", response_model=schemas.ClubFinanceStatus)
def get_specific_club_finances(
    club_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Security check: Ensure the user is an authority
    if current_user.role not in ["authority", "adsa", "dosa", "gensec"]:
        raise HTTPException(status_code=403, detail="Not authorized to view other clubs.")

    # Find the specific club by ID
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club ledger not found.")
    
    remaining = club.total_allocated - club.total_spent
    utilization = (club.total_spent / club.total_allocated) * 100 if club.total_allocated > 0 else 0
    
    return {
        "name": club.name,
        "total_allocated": club.total_allocated,
        "total_spent": club.total_spent,
        "remaining_balance": remaining,
        "utilization_percentage": round(utilization, 2),
        "transactions": club.transactions
    }

# 2. JSON TRANSACTION (Required for your Integration Tests)
@router.post("/transactions", response_model=schemas.TransactionRead)
def submit_json_transaction(
    transaction_data: schemas.TransactionBase, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Use this query in your GET and POST routes in finances.py
    club = db.query(models.Club).filter(
    (models.Club.user_id == current_user.id) | (models.Club.name == current_user.username)
).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club ledger not found.")

    if (club.total_spent + transaction_data.amount) > club.total_allocated:
        raise HTTPException(status_code=400, detail="Insufficient budget!")

    club.total_spent += transaction_data.amount
    new_tx = models.Transaction(
        club_id=club.id,
        amount=transaction_data.amount,
        description=transaction_data.description
    )
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    return new_tx

# 3. UPLOAD BILL (The Real-World Feature with Files)
@router.post("/upload-bill")
async def upload_bill(
    amount: float = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Inside get_my_club_finances and submit_json_transaction
    # Use this query in your GET and POST routes in finances.py
    club = db.query(models.Club).filter(
    (models.Club.user_id == current_user.id) | (models.Club.name == current_user.username)
).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Save the file
    upload_dir = "static/receipts"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_location = f"{upload_dir}/{file.filename}"
    with open(file_location, "wb+") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update budget & log transaction
    club.total_spent += amount
    new_transaction = models.Transaction(
        club_id=club.id,
        amount=amount,
        description=description,
        receipt_url=file_location
    )
    
    db.add(new_transaction)
    db.commit()
    
    return {"message": "Bill uploaded successfully", "receipt_path": file_location}