from datetime import date
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from .database import Base, engine, get_db
from .models import Group, Member, Expense, ExpenseShare, Settlement, Activity
from .schemas import GroupCreate, GroupUpdate, MemberCreate, ExpenseCreate, SettlementCreate
from .services import paise, money, log, balances_for_group, simplify, split_amount

Base.metadata.create_all(bind=engine)
app = FastAPI(title="SplitFlow API", version="1.0.0", description="Group expenses and settle up simply.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://bitshift-six.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def group_or_404(db, group_id):
    group = db.get(Group, group_id)
    if not group: raise HTTPException(404, "Group not found.")
    return group

def expense_json(db, e):
    return {"id": e.id, "group_id": e.group_id, "title": e.title, "amount": money(e.amount_paise), "amount_paise": e.amount_paise, "category": e.category, "payer_id": e.payer_id, "payer_name": e.payer.name, "expense_date": e.expense_date.isoformat(), "description": e.description, "split_method": e.split_method, "shares": [{"member_id": s.member_id, "name": s.member.name, "amount": money(s.amount_paise), "amount_paise": s.amount_paise} for s in e.shares]}

def settlement_json(s):
    return {"id": s.id, "group_id": s.group_id, "payer_id": s.payer_id, "receiver_id": s.receiver_id, "amount": money(s.amount_paise), "payer_name": s.payer.name, "receiver_name": s.receiver.name, "note": s.note, "created_at": s.created_at.isoformat()}

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "SplitFlow"}

@app.get("/api/groups")
def list_groups(db: Session = Depends(get_db)):
    groups = db.scalars(select(Group).options(joinedload(Group.members)).order_by(Group.id.desc())).unique().all()
    result = []
    for g in groups:
        expenses = db.scalars(select(Expense).where(Expense.group_id == g.id)).all()
        result.append({"id": g.id, "name": g.name, "description": g.description, "budget": money(g.budget_paise) if g.budget_paise is not None else None, "members": [{"id": m.id, "name": m.name} for m in g.members], "total_expenses": money(sum(e.amount_paise for e in expenses)), "expense_count": len(expenses)})
    return result

@app.post("/api/groups", status_code=201)
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    group = Group(name=payload.name.strip(), description=payload.description.strip(), budget_paise=paise(payload.budget) if payload.budget else None)
    db.add(group); db.flush()
    names = list(dict.fromkeys(n.strip() for n in payload.members if n.strip()))
    for name in names: db.add(Member(group_id=group.id, name=name))
    log(db, group.id, f'Created group "{group.name}"')
    db.commit(); db.refresh(group)
    return {"id": group.id, "name": group.name, "description": group.description, "budget": money(group.budget_paise) if group.budget_paise is not None else None, "members": [{"id": m.id, "name": m.name} for m in group.members]}

@app.get("/api/groups/{group_id}")
def get_group(group_id: int, db: Session = Depends(get_db)):
    g = group_or_404(db, group_id)
    return {"id": g.id, "name": g.name, "description": g.description, "budget": money(g.budget_paise) if g.budget_paise is not None else None, "members": [{"id": m.id, "name": m.name} for m in g.members]}

@app.put("/api/groups/{group_id}")
def update_group(group_id: int, payload: GroupUpdate, db: Session = Depends(get_db)):
    g = group_or_404(db, group_id)
    data = payload.model_dump(exclude_unset=True)
    if "budget" in data:
        g.budget_paise = paise(data.pop("budget")) if data["budget"] is not None else None
    for key, value in data.items(): setattr(g, key, value)
    log(db, group_id, f'Updated group "{g.name}"')
    db.commit(); db.refresh(g)
    return {"id": g.id, "name": g.name, "description": g.description, "budget": money(g.budget_paise) if g.budget_paise is not None else None, "members": [{"id": m.id, "name": m.name} for m in g.members]}

@app.delete("/api/groups/{group_id}", status_code=204)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = group_or_404(db, group_id)
    db.delete(g); db.commit()
    return Response(status_code=204)

@app.post("/api/groups/{group_id}/members", status_code=201)
def add_member(group_id: int, payload: MemberCreate, db: Session = Depends(get_db)):
    g = group_or_404(db, group_id)
    m = Member(group_id=group_id, name=payload.name.strip())
    db.add(m)
    log(db, group_id, f'Added member "{m.name}"')
    db.commit()
    db.refresh(m)
    return {"id": m.id, "name": m.name}
