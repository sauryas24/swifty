import os
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/mou", tags=["MoU"])

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Endpoint 1: Submit MoU Request
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

    try:
        # 1. Upload the file directly to Cloudinary
        upload_result = cloudinary.uploader.upload(
            document.file,
            folder="swifty_mous", 
            resource_type="auto" # Automatically handles PDFs, images, etc.
        )
        # 2. Extract the permanent secure URL
        secure_url = upload_result.get("secure_url")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

    # 3. Insert a new record into the database containing the permanent URL
    new_mou = models.MoURequest(
        coordinator_id=current_user.id,
        organization_name=organization_name,
        purpose=purpose,
        document_url=secure_url,
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
    mou = db.query(models.MoURequest).filter(models.MoURequest.id == mou_id).first()

    if not mou:
        raise HTTPException(status_code=404, detail="MoU not found")

    return mou