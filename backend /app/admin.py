# admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import auth, models, price_engine
from pydantic import BaseModel

router = APIRouter(prefix="/admin")

class NewsIn(BaseModel):
    title: str
    body: str
    impact: float
    target_ticker: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/news")
def create_news(event: NewsIn, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if not user.is_admin:
        raise HTTPException(403, "admin only")
    ne = models.NewsEvent(title=event.title, body=event.body, impact=event.impact, target_ticker=event.target_ticker, created_by=user.id)
    db.add(ne)
    db.commit()
    # apply immediately (could be scheduled)
    price_engine.apply_news_event(db, ne)
    return {"status":"ok"}
