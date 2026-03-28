import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..utils import security

router = APIRouter(prefix="/api/finances", tags=["finances"])

# 1. GET STATUS (Required for Dashboard & Tests)
# Retrieves the overall budget status and transaction history for the logged-in club coordinator.
@router.get("/status", response_model=schemas.ClubFinanceStatus)
def get_my_club_finances(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Query the database to ensure we only retrieve the club connected to this specific user.
    club = db.query(models.Club).filter(
    (models.Club.user_id == current_user.id) | (models.Club.name == current_user.username)
).first()
    if not club:
        raise HTTPException(status_code=404, detail="Finance ledger not found.")
    
    # Calculate how much money is left and what percentage has been used.
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


# 4. GET SPECIFIC CLUB STATUS (For ADSA Dashboard)
# Allows administrative authorities to view the financial status of any specific club.
@router.get("/{club_id}", response_model=schemas.ClubFinanceStatus)
def get_specific_club_finances(
    club_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Security check: Ensure the user holds an administrative role before allowing access.
    if current_user.role not in ["authority", "adsa", "gensec", "president", "facad"]:
        raise HTTPException(status_code=403, detail="Not authorized to view other clubs.")

    # Locate the club matching the requested ID.
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club ledger not found.")
    
    # Calculate how much money is left and what percentage has been used.
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
# Directly logs a new transaction without requiring a physical receipt file upload.
@router.post("/transactions", response_model=schemas.TransactionRead)
def submit_json_transaction(
    transaction_data: schemas.TransactionBase, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Locate the club associated with the current user.
    club = db.query(models.Club).filter(
    (models.Club.user_id == current_user.id) | (models.Club.name == current_user.username)
).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club ledger not found.")

    # Prevent spending if the transaction exceeds the allocated budget limit.
    if (club.total_spent + transaction_data.amount) > club.total_allocated:
        raise HTTPException(status_code=400, detail="Insufficient budget!")

    # Update the total spent amount and log the new transaction in the database.
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
# Processes physical receipt uploads, saves the file securely, and updates the club's ledger.
# 3. UNIFIED TRANSACTION & UPLOAD ROUTE 
# Handles both coordinators (own club) and authorities (specific club via club_id)
@router.post("/transaction")
async def upload_transaction_receipt(
    amount: float = Form(...),
    description: str = Form(...),
    club_id: int = Form(None),         # Sent by the ADSA frontend
    receipt: UploadFile = File(None),  # Must match the 'receipt' key in JS FormData
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # 1. Determine which club is being billed
    if club_id:
        # Authority uploading for a specific club
        if current_user.role not in ["authority", "adsa", "gensec", "president", "facad"]:
            raise HTTPException(status_code=403, detail="Not authorized to upload bills for other clubs.")
        club = db.query(models.Club).filter(models.Club.id == club_id).first()
    else:
        # Coordinator uploading for their own club
        club = db.query(models.Club).filter(
            (models.Club.user_id == current_user.id) | (models.Club.name == current_user.username)
        ).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # 2. Prevent overspending
    if (club.total_spent + amount) > club.total_allocated:
        raise HTTPException(status_code=400, detail="Insufficient budget available!")

    # 3. Handle the file upload securely
    file_location = None
    if receipt:
        upload_dir = "static/receipts"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        file_location = f"{upload_dir}/{receipt.filename}"
        with open(file_location, "wb+") as buffer:
            shutil.copyfileobj(receipt.file, buffer)

    # 4. Save the transaction to the ledger
    club.total_spent += amount
    new_transaction = models.Transaction(
        club_id=club.id,
        amount=amount,
        description=description,
        receipt_url=file_location
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return {"message": "Transaction logged successfully", "receipt_path": file_location}