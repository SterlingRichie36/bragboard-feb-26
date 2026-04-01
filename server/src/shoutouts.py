from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from src.database import get_db
from src.models import Shoutout

router = APIRouter(prefix="/shoutouts", tags=["Shoutouts"])


class ShoutoutCreate(BaseModel):
    sender_id: int
    recipient_id: int
    message: str


class ReactionUpdate(BaseModel):
    reaction: str


class ShoutoutResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    message: str
    likes: int
    claps: int
    stars: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ShoutoutResponse])
def get_all_shoutouts(db: Session = Depends(get_db)):
    return db.query(Shoutout).order_by(Shoutout.created_at.desc()).all()


@router.get("/employee/{employee_id}", response_model=List[ShoutoutResponse])
def get_shoutouts_by_employee(employee_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Shoutout)
        .filter(Shoutout.recipient_id == employee_id)
        .order_by(Shoutout.created_at.desc())
        .all()
    )


@router.get("/employee/shoutouts/received", response_model=List[ShoutoutResponse])
def get_received(db: Session = Depends(get_db)):
    return db.query(Shoutout).order_by(Shoutout.created_at.desc()).all()


@router.get("/employee/shoutouts/given", response_model=List[ShoutoutResponse])
def get_given(db: Session = Depends(get_db)):
    return db.query(Shoutout).order_by(Shoutout.created_at.desc()).all()


@router.get("/employee/shoutouts/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Shoutout).count()
    return {
        "given": total,
        "received": total,
        "total": total
    }


@router.post("/", response_model=ShoutoutResponse, status_code=status.HTTP_201_CREATED)
def create_shoutout(data: ShoutoutCreate, db: Session = Depends(get_db)):
    if data.sender_id == data.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender and recipient cannot be the same employee"
        )

    shoutout = Shoutout(
        sender_id=data.sender_id,
        recipient_id=data.recipient_id,
        message=data.message,
    )
    db.add(shoutout)
    db.commit()
    db.refresh(shoutout)
    return shoutout


@router.patch("/{shoutout_id}/react", response_model=ShoutoutResponse)
def react_to_shoutout(shoutout_id: int, data: ReactionUpdate, db: Session = Depends(get_db)):
    valid_reactions = {"likes", "claps", "stars"}
    if data.reaction not in valid_reactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid reaction. Must be one of: {valid_reactions}"
        )

    shoutout = db.query(Shoutout).filter(Shoutout.id == shoutout_id).first()
    if not shoutout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shoutout with id {shoutout_id} not found"
        )

    setattr(shoutout, data.reaction, getattr(shoutout, data.reaction) + 1)
    db.commit()
    db.refresh(shoutout)
    return shoutout


@router.delete("/{shoutout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shoutout(shoutout_id: int, db: Session = Depends(get_db)):
    shoutout = db.query(Shoutout).filter(Shoutout.id == shoutout_id).first()
    if not shoutout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shoutout with id {shoutout_id} not found"
        )

    db.delete(shoutout)
    db.commit()