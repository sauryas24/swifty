from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/mou", tags=["MoU"])

# Endpoint 1: Submit MoU Request
@router.post("/submit", response_model=schemas.MoUResponse)
def submit_mou(
    mou_data: schemas.MoUCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Allows a coordinator to submit a new MoU request.
    The default status (e.g., 'pending_gensec') should be handled in models.py.
    """
    if current_user.role != "coordinator":
        raise HTTPException(status_code=403, detail="Only coordinators can submit MoU requests")

    new_mou = models.MoURequest(
        coordinator_id=current_user.id,
        organization_name=mou_data.organization_name,
        purpose=mou_data.purpose,
        document_url=mou_data.document_url
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