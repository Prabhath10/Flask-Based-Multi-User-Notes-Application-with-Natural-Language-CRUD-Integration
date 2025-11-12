# models.py
from datetime import datetime
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, ForeignKey, Text)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///notes.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # in real apps, hash the password!
    last_login = Column(DateTime, default=None)

    notes = relationship("Note", back_populates="user", cascade="all, delete")

class Note(Base):
    __tablename__ = "notes"
    note_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    topic = Column(String)
    message = Column(Text)
    last_update = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notes")

def init_db():
    Base.metadata.create_all(bind=engine)
