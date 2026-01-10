import datetime

from sqlalchemy import BigInteger, Integer,  String, DateTime,  Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column, relationship
from .database import Base
from datetime import  datetime, date, time
from typing import Optional


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True, nullable=False, autoincrement=True) 
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    institute: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    group: Mapped[str] = mapped_column(String, nullable=False)
    course: Mapped[int] = mapped_column(Integer, nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    tiukoins: Mapped[float] = mapped_column(Float, nullable=False)
    approval_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    moderator_username: Mapped[str] = mapped_column(String, nullable=False)

    event_applications: Mapped[list["Event_applications"]] = relationship(
        "Event_applications", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
class Event_applications(Base):
    __tablename__='event_applications'
    id: Mapped[int]=mapped_column(BigInteger,nullable=False, primary_key = True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey('users.tg_id'),  
        nullable=False
    )
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    event_direction: Mapped[str] = mapped_column(String, nullable=False)
    event_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_event: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    event_place: Mapped[str] = mapped_column(String, nullable=False)
    event_role: Mapped[str] = mapped_column(String, nullable=False)

    role_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey('roles.id'), 
        nullable=False
    )
    event_application_status: Mapped[str] = mapped_column(String, nullable=False)
    amount_tiukoins: Mapped[float] = mapped_column(Float, nullable=False)
    moderator: Mapped[str] = mapped_column(String, nullable=False)
  
    user: Mapped["Users"] = relationship("Users", back_populates="event_applications") 
    role: Mapped["Roles"] = relationship("Roles", back_populates="event_applications")

class Roles(Base):
    __tablename__='roles'
    id: Mapped[int]=mapped_column(BigInteger,primary_key = True, autoincrement=True)
    role: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    base_value_tiukoins: Mapped[float] = mapped_column(Float, nullable=False)

    event_applications: Mapped[list["Event_applications"]] = relationship(
        "Event_applications", 
        back_populates="role"
    )
