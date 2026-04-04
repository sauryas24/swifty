import os
import cloudinary
import cloudinary.uploader
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..utils import security

router = APIRouter(prefix="/api/finances", tags=["finances"])

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# 1. GET STATUS 
@router.get("/status", response_model=schemas.ClubFinanceStatus)
def get_my_club_finances(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    club = db.query(models.Club).filter(
        (models.Club.user_id == current_user.id) | (models.Club.name == current_user.username)
    ).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Finance ledger not found.")
    
    # --- NEW: Auto-Heal Discrepancies ---
    # Calculate the true total based ONLY on existing transaction records
    actual_spent = sum(tx.amount for tx in club.transactions)
    
    # If the database tracker is out of sync, fix it automatically
    if club.total_spent != actual_spent:
        club.total_spent = actual_spent
        db.commit()
        db.refresh(club)
    # ------------------------------------
    
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

# 4. GET SPECIFIC CLUB STATUS 
@router.get("/{club_id}", response_model=schemas.ClubFinanceStatus)
def get_specific_club_finances(
    club_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    if current_user.role not in ["authority", "adsa", "gensec", "president", "facad"]:
        raise HTTPException(status_code=403, detail="Not authorized to view other clubs.")

    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club ledger not found.")
    
    # --- NEW: Auto-Heal Discrepancies ---
    actual_spent = sum(tx.amount for tx in club.transactions)
    if club.total_spent != actual_spent:
        club.total_spent = actual_spent
        db.commit()
        db.refresh(club)
    # ------------------------------------
    
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

# 2. JSON TRANSACTION 
@router.post("/transactions", response_model=schemas.TransactionRead)
def submit_json_transaction(
    transaction_data: schemas.TransactionBase, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
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

# 3. UNIFIED TRANSACTION & UPLOAD ROUTE 
@router.post("/transaction")
async def upload_transaction_receipt(
    amount: float = Form(...),
    description: str = Form(...),
    club_id: int = Form(None),         
    receipt: UploadFile = File(None),  
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # 1. Determine which club is being billed
    if club_id:
        if current_user.role not in ["authority", "adsa", "gensec", "president", "facad"]:
            raise HTTPException(status_code=403, detail="Not authorized to upload bills for other clubs.")
        club = db.query(models.Club).filter(models.Club.id == club_id).first()
    else:
        club = db.query(models.Club).filter(
            (models.Club.user_id == current_user.id) | (models.Club.name == current_user.username)
        ).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # 2. Prevent overspending
    if (club.total_spent + amount) > club.total_allocated:
        raise HTTPException(status_code=400, detail="Insufficient budget available!")

    # 3. Handle the Cloudinary file upload securely
    secure_url = None
    if receipt:
        try:
            upload_result = cloudinary.uploader.upload(
                receipt.file,
                folder="swifty_receipts", 
                resource_type="auto"
            )
            secure_url = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

    # 4. Save the transaction to the ledger with the Cloudinary URL
    club.total_spent += amount
    new_transaction = models.Transaction(
        club_id=club.id,
        amount=amount,
        description=description,
        receipt_url=secure_url
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return {"message": "Transaction logged successfully", "receipt_path": secure_url}