import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/mou", tags=["MoU"])

# Endpoint 1: Submit MoU Request
# Allows a club coordinator to securely upload an MoU document for administrative approval.
@router.post("/submit", response_model=schemas.MoUResponse)
def submit_mou(
    organization_name: str = Form(...),
    purpose: str = Form(...),
    document: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Verify that only a coordinator is making this request.
    if current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Only coordinators can submit MoU requests")

    # 1. Ensure the target directory for documents is available.
    os.makedirs("static/mou_documents", exist_ok=True)

    # 2. Assign a unique name to the file to prevent overwriting existing documents.
    file_extension = document.filename.split(".")[-1]
    safe_filename = f"{uuid.uuid4()}.{file_extension}"
    file_location = f"static/mou_documents/{safe_filename}"

    # 3. Securely write the file to the hard drive.
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(document.file, file_object)

    # 4. Insert a new record into the database containing the MoU details and file path.
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
# Fetches the details of a single MoU, commonly used when checking its review progress.
@router.get("/{mou_id}", response_model=schemas.MoUResponse)
def get_mou(
    mou_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Look up the MoU by its ID number.
    mou = db.query(models.MoURequest).filter(models.MoURequest.id == mou_id).first()

    if not mou:
        raise HTTPException(status_code=404, detail="MoU not found")

    return mou