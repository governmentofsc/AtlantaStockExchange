# trading.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models, auth, price_engine
from pydantic import BaseModel

router = APIRouter(prefix="/trade")

class TradeIn(BaseModel):
    ticker: str
    side: str  # BUY or SELL
    quantity: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def place_trade(trade: TradeIn, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    ticker = trade.ticker.upper()
    stock = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(404, "Ticker not found")
    qty = int(trade.quantity)
    if qty <= 0:
        raise HTTPException(400, "Quantity must be positive")

    # Simple order execution at current_price
    price = stock.current_price
    total = price * qty

    if trade.side == "BUY":
        if user.balance < total:
            raise HTTPException(400, "Insufficient balance")
        user.balance -= total
        # find or create holding
        holding = db.query(models.Holding).filter_by(user_id=user.id, stock_id=stock.id).first()
        if not holding:
            holding = models.Holding(user_id=user.id, stock_id=stock.id, shares=0)
            db.add(holding)
        holding.shares += qty
        # record trade
        t = models.Trade(user_id=user.id, stock_id=stock.id, side="BUY", quantity=qty, price=price)
        db.add(t)
        # affect market
        price_engine.record_trade(db, stock, buy_volume=qty, sell_volume=0)
    elif trade.side == "SELL":
        holding = db.query(models.Holding).filter_by(user_id=user.id, stock_id=stock.id).first()
        if not holding or holding.shares < qty:
            raise HTTPException(400, "Not enough shares")
        holding.shares -= qty
        user.balance += total
        t = models.Trade(user_id=user.id, stock_id=stock.id, side="SELL", quantity=qty, price=price)
        db.add(t)
        price_engine.record_trade(db, stock, buy_volume=0, sell_volume=qty)
    else:
        raise HTTPException(400, "Invalid side")
    db.commit()
    return {"status": "ok", "price": price}
