import datetime

from sqlalchemy import BigInteger, Integer,  String, DateTime,  Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column, relationship
from .database import Base
from datetime import  datetime
from typing import Optional


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key = True, nullable=False, autoincrement=True) 
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
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
    username: Mapped[str] = mapped_column(String, nullable=False)
    event_direction: Mapped[str] = mapped_column(String, nullable=False)
    event_name: Mapped[str] = mapped_column(String, nullable=False)
    date_of_event: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    event_place: Mapped[str] = mapped_column(String, nullable=False)
    event_role: Mapped[str] = mapped_column(String, nullable=False)

    
    event_application_status: Mapped[str] = mapped_column(String, nullable=False)
    amount_tiukoins: Mapped[float] = mapped_column(Float, nullable=False)
    moderator: Mapped[str] = mapped_column(String, nullable=False)
  
    user: Mapped["Users"] = relationship("Users", back_populates="event_applications") 
    

class Roles(Base):
    __tablename__='roles'
    id: Mapped[int]=mapped_column(BigInteger,primary_key = True, autoincrement=True)
    role: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    base_value_tiukoins: Mapped[float] = mapped_column(Float, nullable=False)


class Catalog_of_reward(Base):
    __tablename__ = "catalog_of_reward"
    id: Mapped[int]=mapped_column(BigInteger,nullable=False, primary_key = True, autoincrement=True)
    name_of_reward: Mapped[str] = mapped_column(String, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str] = mapped_column(String, nullable=False)
    link_on_photo: Mapped[str] = mapped_column(String, nullable=True)


    issuances: Mapped[list["Issuance_of_rewards"]] = relationship(
        back_populates="reward", 
    )
    
class Issuance_of_rewards(Base):
    __tablename__ = "issuance_of_rewards"
    id: Mapped[int]=mapped_column(BigInteger,nullable=False, primary_key = True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    reward_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("catalog_of_reward.id", ondelete="SET NULL"), 
        nullable=True
    )
    name_of_reward:Mapped[str] = mapped_column(String, nullable=False)
    price:Mapped[int] = mapped_column(Integer, nullable=False)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    moderator_username: Mapped[str] = mapped_column(String, nullable=False)

    reward: Mapped[Optional["Catalog_of_reward"]] = relationship(
        back_populates="issuances"
    )