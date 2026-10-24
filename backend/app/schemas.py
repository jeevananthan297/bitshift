from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class MemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class MemberOut(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    budget: float | None = Field(default=None, gt=0)
    members: list[str] = []

class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    budget: float | None = Field(default=None, gt=0)

class GroupOut(BaseModel):
    id: int
    name: str
    description: str
    budget: float | None
    members: list[MemberOut]
    model_config = ConfigDict(from_attributes=True)

class ShareInput(BaseModel):
    member_id: int
    value: float = Field(ge=0)

class ExpenseCreate(BaseModel):
    group_id: int
    title: str = Field(min_length=1, max_length=150)
    amount: float = Field(gt=0)
    category: str = "other"
    payer_id: int
    expense_date: date | None = None
    description: str = ""
    split_method: Literal["equal", "exact", "percentage", "shares"] = "equal"
    participants: list[ShareInput] = Field(min_length=1)

class ExpenseOut(BaseModel):
    id: int
    group_id: int
    title: str
    amount: float
    amount_paise: int
    category: str
    payer_id: int
    payer_name: str
    expense_date: date
    description: str
    split_method: str
    shares: list[dict]
    model_config = ConfigDict(from_attributes=True)

class SettlementCreate(BaseModel):
    group_id: int
    payer_id: int
    receiver_id: int
    amount: float = Field(gt=0)
    note: str = ""

class SettlementOut(BaseModel):
    id: int
    group_id: int
    payer_id: int
    receiver_id: int
    amount: float
    payer_name: str
    receiver_name: str
    note: str
    created_at: datetime

class ActivityOut(BaseModel):
    id: int
    group_id: int
    message: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
