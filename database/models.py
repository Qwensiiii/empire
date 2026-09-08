from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    balance = Column(Float, default=0.0)
    click_power = Column(Integer, default=1)
    total_clicks = Column(Integer, default=0)
    total_earned = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_click = Column(DateTime)
    last_income = Column(DateTime)
    
    businesses = relationship("Business", back_populates="owner")
    shares = relationship("Share", back_populates="user")

class Business(Base):
    __tablename__ = 'businesses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    emoji = Column(String(10), default='🏪')
    price = Column(Float, nullable=False)
    income_per_hour = Column(Float, nullable=False)
    level = Column(Integer, default=1)
    max_level = Column(Integer, default=10)
    owner_id = Column(BigInteger, ForeignKey('users.user_id'))
    purchased_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="businesses")
    shares = relationship("Share", back_populates="business")

class Share(Base):
    __tablename__ = 'shares'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    business_id = Column(Integer, ForeignKey('businesses.id'))
    quantity = Column(Integer, default=1)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="shares")
    business = relationship("Business", back_populates="shares")

class ClickHistory(Base):
    __tablename__ = 'click_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    clicks = Column(Integer, default=0)
    earned = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)