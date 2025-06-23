from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from . import models, schemas
from .db import get_db

router = APIRouter()

@router.post("/requests/", response_model=schemas.LeaveRequest)
def create_leave_request(request: schemas.LeaveRequestCreate, db: Session = Depends(get_db)):
    db_request = models.LeaveRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.get("/requests/{request_id}", response_model=schemas.LeaveRequest)
def read_leave_request(request_id: int, db: Session = Depends(get_db)):
    return db.query(models.LeaveRequest).filter(models.LeaveRequest.id == request_id).first()
