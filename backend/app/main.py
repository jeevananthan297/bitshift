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
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
    db.add(m); log(db, group_id, f'Added member "{m.name}"')
    db.commit(); db.refresh(m)
    return {"id": m.id, "name": m.name}

@app.delete("/api/groups/{group_id}/members/{member_id}", status_code=204)
def delete_member(group_id: int, member_id: int, db: Session = Depends(get_db)):
    m = db.scalar(select(Member).where(Member.id == member_id, Member.group_id == group_id))
    if not m: raise HTTPException(404, "Member not found in this group.")
    if db.scalar(select(Expense).where(Expense.group_id == group_id, Expense.payer_id == member_id)) or db.scalar(select(ExpenseShare).join(Expense).where(Expense.group_id == group_id, ExpenseShare.member_id == member_id)) or db.scalar(select(Settlement).where(Settlement.group_id == group_id).where((Settlement.payer_id == member_id) | (Settlement.receiver_id == member_id))):
        raise HTTPException(409, "This member has financial history and cannot be removed.")
    db.delete(m); log(db, group_id, f'Removed member "{m.name}"'); db.commit()
    return Response(status_code=204)

@app.get("/api/expenses")
def list_expenses(group_id: int | None = None, q: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Expense).options(joinedload(Expense.payer), joinedload(Expense.shares).joinedload(ExpenseShare.member)).order_by(Expense.expense_date.desc(), Expense.id.desc())
    if group_id: stmt = stmt.where(Expense.group_id == group_id)
    expenses = db.scalars(stmt).unique().all()
    if q: expenses = [e for e in expenses if q.lower() in e.title.lower() or q.lower() in e.category.lower()]
    return [expense_json(db, e) for e in expenses]

@app.post("/api/expenses", status_code=201)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    g = group_or_404(db, payload.group_id)
    member_ids = {m.id for m in g.members}
    ids = [p.member_id for p in payload.participants]
    if payload.payer_id not in member_ids: raise HTTPException(400, "Payer must belong to this group.")
    if any(i not in member_ids for i in ids): raise HTTPException(400, "Every participant must belong to this group.")
    try: shares = split_amount(paise(payload.amount), [p.model_dump() for p in payload.participants], payload.split_method)
    except ValueError as exc: raise HTTPException(400, str(exc))
    e = Expense(group_id=g.id, title=payload.title.strip(), amount_paise=paise(payload.amount), category=payload.category, payer_id=payload.payer_id, expense_date=payload.expense_date or date.today(), description=payload.description, split_method=payload.split_method)
    db.add(e); db.flush()
    for mid, amount in shares.items(): db.add(ExpenseShare(expense_id=e.id, member_id=mid, amount_paise=amount))
    log(db, g.id, f'Added expense "{e.title}" — ₹{money(e.amount_paise):.2f}')
    db.commit()
    e = db.scalar(select(Expense).options(joinedload(Expense.payer), joinedload(Expense.shares).joinedload(ExpenseShare.member)).where(Expense.id == e.id))
    return expense_json(db, e)

@app.put("/api/expenses/{expense_id}")
def update_expense(expense_id: int, payload: ExpenseCreate, db: Session = Depends(get_db)):
    e = db.get(Expense, expense_id)
    if not e: raise HTTPException(404, "Expense not found.")
    if payload.group_id != e.group_id: raise HTTPException(400, "Moving an expense between groups is not supported.")
    g = group_or_404(db, payload.group_id)
    ids = {m.id for m in g.members}
    if payload.payer_id not in ids or any(p.member_id not in ids for p in payload.participants): raise HTTPException(400, "Payer and participants must belong to the group.")
    try: shares = split_amount(paise(payload.amount), [p.model_dump() for p in payload.participants], payload.split_method)
    except ValueError as exc: raise HTTPException(400, str(exc))
    e.title=payload.title.strip(); e.amount_paise=paise(payload.amount); e.category=payload.category; e.payer_id=payload.payer_id; e.expense_date=payload.expense_date or date.today(); e.description=payload.description; e.split_method=payload.split_method
    e.shares.clear(); db.flush()
    for mid, amount in shares.items(): e.shares.append(ExpenseShare(member_id=mid, amount_paise=amount))
    log(db, g.id, f'Updated expense "{e.title}"'); db.commit()
    e = db.scalar(select(Expense).options(joinedload(Expense.payer), joinedload(Expense.shares).joinedload(ExpenseShare.member)).where(Expense.id == expense_id))
    return expense_json(db, e)

@app.delete("/api/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    e = db.get(Expense, expense_id)
    if not e: raise HTTPException(404, "Expense not found.")
    group_id, title = e.group_id, e.title
    log(db, group_id, f'Deleted expense "{title}"')
    db.delete(e); db.commit()
    return Response(status_code=204)

@app.get("/api/groups/{group_id}/balances")
def get_balances(group_id: int, db: Session = Depends(get_db)):
    group_or_404(db, group_id)
    return balances_for_group(db, group_id)

@app.get("/api/groups/{group_id}/settlement-plan")
def settlement_plan(group_id: int, db: Session = Depends(get_db)):
    group_or_404(db, group_id)
    return simplify(balances_for_group(db, group_id))

@app.post("/api/settlements", status_code=201)
def create_settlement(payload: SettlementCreate, db: Session = Depends(get_db)):
    g = group_or_404(db, payload.group_id)
    ids = {m.id for m in g.members}
    if payload.payer_id not in ids or payload.receiver_id not in ids: raise HTTPException(400, "Both members must belong to the group.")
    if payload.payer_id == payload.receiver_id: raise HTTPException(400, "Payer and receiver must be different.")
    amount = paise(payload.amount)
    if amount <= 0: raise HTTPException(400, "Amount must be positive.")
    balances = {b["member_id"]: b["balance_paise"] for b in balances_for_group(db, g.id)}
    plan = simplify(balances_for_group(db, g.id))
    allowed = sum(p["amount_paise"] for p in plan if p["payer_id"] == payload.payer_id and p["receiver_id"] == payload.receiver_id)
    if amount > allowed: raise HTTPException(400, f"That repayment exceeds the suggested outstanding amount of ₹{money(allowed):.2f}.")
    s = Settlement(group_id=g.id, payer_id=payload.payer_id, receiver_id=payload.receiver_id, amount_paise=amount, note=payload.note)
    db.add(s)
    payer = next(m.name for m in g.members if m.id == payload.payer_id)
    receiver = next(m.name for m in g.members if m.id == payload.receiver_id)
    log(db, g.id, f'{payer} paid {receiver} ₹{money(amount):.2f}')
    db.commit(); db.refresh(s)
    return settlement_json(s)

@app.get("/api/groups/{group_id}/settlements")
def list_settlements(group_id: int, db: Session = Depends(get_db)):
    group_or_404(db, group_id)
    rows = db.scalars(select(Settlement).options(joinedload(Settlement.payer), joinedload(Settlement.receiver)).where(Settlement.group_id == group_id).order_by(Settlement.id.desc())).unique().all()
    return [settlement_json(s) for s in rows]

@app.get("/api/groups/{group_id}/activity")
def group_activity(group_id: int, db: Session = Depends(get_db)):
    group_or_404(db, group_id)
    rows = db.scalars(select(Activity).where(Activity.group_id == group_id).order_by(Activity.id.desc()).limit(50)).all()
    return [{"id": a.id, "group_id": a.group_id, "message": a.message, "created_at": a.created_at.isoformat()} for a in rows]

@app.get("/api/groups/{group_id}/analytics")
def analytics(group_id: int, db: Session = Depends(get_db)):
    g = group_or_404(db, group_id)
    expenses = db.scalars(select(Expense).where(Expense.group_id == group_id)).all()
    category = {}
    month = {}
    for e in expenses:
        category[e.category] = category.get(e.category, 0) + e.amount_paise
        key = e.expense_date.strftime("%Y-%m")
        month[key] = month.get(key, 0) + e.amount_paise
    total = sum(e.amount_paise for e in expenses)
    budget = g.budget_paise
    return {"total_spending": money(total), "budget": money(budget) if budget is not None else None, "budget_remaining": money(budget-total) if budget is not None else None, "budget_percent": round(total / budget * 100, 1) if budget else None, "by_category": [{"category": k, "amount": money(v)} for k,v in sorted(category.items(), key=lambda x:x[1], reverse=True)], "by_month": [{"month": k, "amount": money(v)} for k,v in sorted(month.items())], "expense_count": len(expenses)}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    groups = db.scalars(select(Group).options(joinedload(Group.members))).unique().all()
    total = 0
    group_items = []
    recent = []
    all_category = {}
    for g in groups:
        exps = db.scalars(select(Expense).options(joinedload(Expense.payer), joinedload(Expense.shares).joinedload(ExpenseShare.member)).where(Expense.group_id == g.id).order_by(Expense.id.desc())).unique().all()
        group_total = sum(e.amount_paise for e in exps); total += group_total
        group_items.append({"id":g.id,"name":g.name,"description":g.description,"budget":money(g.budget_paise) if g.budget_paise is not None else None,"members":[{"id":m.id,"name":m.name} for m in g.members],"total_expenses":money(group_total),"expense_count":len(exps)})
        for e in exps:
            all_category[e.category] = all_category.get(e.category,0)+e.amount_paise
            recent.append({"id":e.id,"group_id":g.id,"group_name":g.name,"title":e.title,"amount":money(e.amount_paise),"category":e.category,"payer_name":e.payer.name,"expense_date":e.expense_date.isoformat()})
    recent.sort(key=lambda x:(x["expense_date"],x["id"]), reverse=True)
    return {"total_expenses":money(total),"group_count":len(groups),"groups":group_items,"recent_expenses":recent[:8],"by_category":[{"category":k,"amount":money(v)} for k,v in sorted(all_category.items(),key=lambda x:x[1],reverse=True)]}

@app.post("/api/demo/seed")
def seed_demo(db: Session = Depends(get_db)):
    if db.scalar(select(Group).limit(1)):
        return {"message":"Database already contains data; seed skipped."}
    g = Group(name="Weekend in Pondicherry", description="A getaway with friends", budget_paise=2500000)
    db.add(g); db.flush()
    members = [Member(group_id=g.id,name=n) for n in ["Aarav","Diya","Kabir","Meera"]]
    db.add_all(members); db.flush()
    # Create demo expenses using same allocation service.
    samples = [
        ("Villa booking",12000,"accommodation",members[0],members),
        ("Dinner by the beach",3200,"food",members[1],members),
        ("Fuel",1800,"travel",members[2],members[:3]),
        ("Groceries",950,"groceries",members[3],members),
    ]
    for title, amount, category, payer, participants in samples:
        total_paise = paise(amount)
        allocation = split_amount(total_paise,[{"member_id":m.id,"value":1} for m in participants],"equal")
        e=Expense(group_id=g.id,title=title,amount_paise=total_paise,category=category,payer_id=payer.id,expense_date=date.today(),split_method="equal")
        db.add(e); db.flush()
        for mid, share in allocation.items(): db.add(ExpenseShare(expense_id=e.id,member_id=mid,amount_paise=share))
        log(db,g.id,f'Added demo expense "{title}"')
    log(db,g.id,"Created demo group")
    db.commit()
    return {"message":"Demo group created.","group_id":g.id}

@app.get("/api/expenses/export.csv")
def export_csv(group_id: int | None = None, db: Session = Depends(get_db)):
    import csv, io
    stmt = select(Expense).options(joinedload(Expense.payer)).order_by(Expense.expense_date.desc())
    if group_id: stmt = stmt.where(Expense.group_id == group_id)
    rows = db.scalars(stmt).unique().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Expense ID","Group ID","Title","Date","Category","Payer","Amount"])
    for e in rows:
        writer.writerow([e.id,e.group_id,e.title,e.expense_date.isoformat(),e.category,e.payer.name,f"{money(e.amount_paise):.2f}"])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=splitflow-expenses.csv"})
