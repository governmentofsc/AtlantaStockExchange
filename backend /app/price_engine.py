# price_engine.py
import math, random, threading, time
from sqlalchemy.orm import Session
from . import models, websocket_broadcast
from .database import SessionLocal

# This keeps a small in-memory order-pressure buffer that background thread consumes.
ORDER_IMPACT_FACTOR = 0.0005  # tune this
RANDOM_DRIFT = 0.0002

def record_trade(db: Session, stock: models.Stock, buy_volume:int=0, sell_volume:int=0):
    # increment stock volume and store immediate order pressure in a transient record (DB or memory)
    stock.volume += buy_volume + sell_volume
    db.add(stock)
    db.flush()
    # append to a simple table or in-memory structure; we'll store simple pending impact rows in DB using PricePoint or event table
    # For simplicity we'll apply immediate small impact:
    delta = (buy_volume - sell_volume) * ORDER_IMPACT_FACTOR
    stock.current_price *= (1 + delta)
    # ensure price floor
    stock.current_price = max(stock.current_price, 0.01)
    # persist price point
    pp = models.PricePoint(stock_id=stock.id, price=stock.current_price)
    db.add(pp)
    db.commit()
    # notify websocket clients:
    websocket_broadcast.broadcast_price(stock.ticker, stock.current_price)

def apply_news_event(db: Session, event: models.NewsEvent):
    if event.target_ticker == "ALL":
        stocks = db.query(models.Stock).all()
    else:
        stocks = db.query(models.Stock).filter(models.Stock.ticker == event.target_ticker).all()
    for s in stocks:
        s.current_price *= (1 + event.impact)
        db.add(s)
        db.flush()
        db.add(models.PricePoint(stock_id=s.id, price=s.current_price))
    db.commit()
    # broadcast changes
    for s in stocks:
        websocket_broadcast.broadcast_price(s.ticker, s.current_price)

def background_price_worker():
    while True:
        db = SessionLocal()
        try:
            stocks = db.query(models.Stock).all()
            for s in stocks:
                # geometric brownian-ish perturbation
                z = random.gauss(0, 1)
                dt = 1/252
                mu = RANDOM_DRIFT
                sigma = s.volatility
                s.current_price *= math.exp((mu - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z)
                s.current_price = max(s.current_price, 0.01)
                db.add(s)
                db.flush()
                db.add(models.PricePoint(stock_id=s.id, price=s.current_price))
            db.commit()
            # broadcast all current prices (compact)
            for s in stocks:
                websocket_broadcast.broadcast_price(s.ticker, s.current_price)
        finally:
            db.close()
        time.sleep(5)  # run every 5s; tune as needed

# Start worker thread on import
threading.Thread(target=background_price_worker, daemon=True).start()
