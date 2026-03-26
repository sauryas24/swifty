import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/mou", tags=["MoU"])

# Endpoint 1: Submit MoU Request
@router.post("/submit", response_model=schemas.MoUResponse)
def submit_mou(
    organization_name: str = Form(...),
    purpose: str = Form(...),
    document: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Allows a coordinator to submit a new MoU request and saves the attached document.
    """
    if current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Only coordinators can submit MoU requests")

    # 1. Ensure the directory exists
    os.makedirs("static/mou_documents", exist_ok=True)

    # 2. Generate a safe, unique filename
    # Example: "Draft.pdf" becomes "123e4567-e89b-12d3-a456-426614174000.pdf"
    file_extension = document.filename.split(".")[-1]
    safe_filename = f"{uuid.uuid4()}.{file_extension}"
    file_location = f"static/mou_documents/{safe_filename}"

    # 3. Save the file to the static directory
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(document.file, file_object)

    # 4. Save the record to the database
    new_mou = models.MoURequest(
        coordinator_id=current_user.id,
        organization_name=organization_name,
        purpose=purpose,
        document_url=file_location,
        status="Pending GenSec"  
    )

    db.add(new_mou)
    db.commit()
    db.refresh(new_mou)

    return new_mou


# Endpoint 2: Get specific MoU status
@router.get("/{mou_id}", response_model=schemas.MoUResponse)
def get_mou(
    mou_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Fetches the details of a specific MoU by its ID.
    """
    mou = db.query(models.MoURequest).filter(models.MoURequest.id == mou_id).first()

    if not mou:
        raise HTTPException(status_code=404, detail="MoU not found")

    return mou