from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, models, schemas
from ..utils import security

router = APIRouter(prefix="/api/mou", tags=["MoU"])

# Submit MoU Request
@router.post("/submit", response_model=schemas.MoUResponse)
def submit_mou(
    mou_data: schemas.MoUCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):

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


# Get all MoU requests
@router.get("/all", response_model=list[schemas.MoUResponse])
def get_all_mous(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):

    mous = db.query(models.MoURequest).all()
    return mous


# Get MoU status
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


# Approval Flow
@router.post("/approve")
def approve_mou(
    approval: schemas.MoUApproval,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):

    mou = db.query(models.MoURequest).filter(models.MoURequest.id == approval.mou_id).first()

    if not mou:
        raise HTTPException(status_code=404, detail="MoU not found")

    if approval.action == "reject":
        mou.status = "rejected"
        mou.comments = approval.comments

    elif approval.action == "approve":

        if current_user.role == "gensec" and mou.status == "pending_gensec":
            mou.status = "pending_faculty"

        elif current_user.role == "faculty" and mou.status == "pending_faculty":
            mou.status = "pending_adsa"

        elif current_user.role == "adsa" and mou.status == "pending_adsa":
            mou.status = "approved"

        else:
            raise HTTPException(status_code=403, detail="Invalid approval step")

    db.commit()

    return {"message": "MoU updated successfully", "status": mou.status}

#if approvals.py doing this shit, then remove this last function