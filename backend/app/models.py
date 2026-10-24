from datetime import date, datetime, timezone
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(300), default="")
    budget_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    members = relationship("Member", back_populates="group", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")
    settlements = relationship("Settlement", back_populates="group", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="group", cascade="all, delete-orphan")

class Member(Base):
    __tablename__ = "members"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    group = relationship("Group", back_populates="members")

class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="other")
    payer_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, default=date.today)
    description: Mapped[str] = mapped_column(Text, default="")
    split_method: Mapped[str] = mapped_column(String(20), default="equal")
    group = relationship("Group", back_populates="expenses")
    shares = relationship("ExpenseShare", back_populates="expense", cascade="all, delete-orphan")
    payer = relationship("Member", foreign_keys=[payer_id])

class ExpenseShare(Base):
    __tablename__ = "expense_shares"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id", ondelete="CASCADE"), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    expense = relationship("Expense", back_populates="shares")
    member = relationship("Member")

class Settlement(Base):
    __tablename__ = "settlements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    payer_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str] = mapped_column(String(250), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    group = relationship("Group", back_populates="settlements")
    payer = relationship("Member", foreign_keys=[payer_id])
    receiver = relationship("Member", foreign_keys=[receiver_id])

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    group = relationship("Group", back_populates="activities")
