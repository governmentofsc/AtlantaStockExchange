# models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    discord_id = Column(String, unique=True, nullable=True)
    balance = Column(Float, default=10000.0)
    is_admin = Column(Boolean, default=False)
    holdings = relationship("Holding", back_populates="user")

class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    current_price = Column(Float, default=10.0)
    volatility = Column(Float, default=0.02)  # daily vol proxy
    volume = Column(Integer, default=0)
    history = relationship("PricePoint", back_populates="stock")

class Holding(Base):
    __tablename__ = "holdings"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), primary_key=True)
    shares = Column(Integer, default=0)
    user = relationship("User", back_populates="holdings")
    stock = relationship("Stock")

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    side = Column(String)  # BUY / SELL
    quantity = Column(Integer)
    price = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class PricePoint(Base):
    __tablename__ = "price_points"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    price = Column(Float)
    stock = relationship("Stock", back_populates="history")

class NewsEvent(Base):
    __tablename__ = "news_events"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(String)
    impact = Column(Float)  # proportion change e.g. 0.1 = +10%
    target_ticker = Column(String)  # or 'ALL'
    created_by = Column(Integer, ForeignKey("users.id"))
