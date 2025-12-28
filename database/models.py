import datetime

from sqlalchemy import BigInteger, Integer,  String, DateTime,  Float
from sqlalchemy.orm import relationship, Mapped, mapped_column, relationship
from .database import Base
from datetime import  datetime, date, time
from typing import Optional



class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True, nullable=False, autoincrement=True) 
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    institute: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    group: Mapped[str] = mapped_column(String, nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    tiucoins: Mapped[float] = mapped_column(Float, nullable=False)
    approval_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    moderator_username: Mapped[str] = mapped_column(String, nullable=False)

    event_applications: Mapped[list["Event_applications"]] = relationship("Event_applications", back_populates="users")

class Event_applications(Base):
    __tablename__='event_applications'
    id: Mapped[int]=mapped_column(BigInteger,nullable=False, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key = True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    event_direction: Mapped[str] = mapped_column(String, nullable=False)
    event_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_event: Mapped[datetime] = mapped_column(DateTime, nullbale=False)
    event_place: Mapped[str] = mapped_column(String, nullable=False)
    event_role: Mapped[str] = mapped_column(String, nullable=False)
    event_application_status: Mapped[str] = mapped_column(String, nullable=False)
  
    user: Mapped["Users"] = relationship("Users", back_populates="event_applications") 
