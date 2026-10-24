from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import Group, Member, Expense, ExpenseShare, Settlement, Activity

def paise(value: float) -> int:
    # Values arrive as decimal currency; convert to integer paise deterministically.
    return int(round(value * 100))

def money(value: int) -> float:
    return round(value / 100, 2)

def log(db: Session, group_id: int, message: str):
    db.add(Activity(group_id=group_id, message=message))

def balances_for_group(db: Session, group_id: int):
    group = db.get(Group, group_id)
    if not group:
        return None
    balances = {m.id: 0 for m in group.members}
    for expense in db.scalars(select(Expense).where(Expense.group_id == group_id)).all():
        balances[expense.payer_id] += expense.amount_paise
        for share in expense.shares:
            balances[share.member_id] -= share.amount_paise
    for settlement in db.scalars(select(Settlement).where(Settlement.group_id == group_id)).all():
        # A payer settles debt by sending money to a receiver.
        balances[settlement.payer_id] += settlement.amount_paise
        balances[settlement.receiver_id] -= settlement.amount_paise
    return [{"member_id": m.id, "name": m.name, "balance": money(balances[m.id]), "balance_paise": balances[m.id]} for m in group.members]

def simplify(balances):
    creditors = [[b["member_id"], b["name"], int(b["balance_paise"])] for b in balances if b["balance_paise"] > 0]
    debtors = [[b["member_id"], b["name"], -int(b["balance_paise"])] for b in balances if b["balance_paise"] < 0]
    creditors.sort(key=lambda x: x[2], reverse=True)
    debtors.sort(key=lambda x: x[2], reverse=True)
    result = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        amount = min(debtors[i][2], creditors[j][2])
        if amount:
            result.append({
                "payer_id": debtors[i][0], "payer_name": debtors[i][1],
                "receiver_id": creditors[j][0], "receiver_name": creditors[j][1],
                "amount": money(amount), "amount_paise": amount
            })
        debtors[i][2] -= amount
        creditors[j][2] -= amount
        if debtors[i][2] == 0: i += 1
        if creditors[j][2] == 0: j += 1
    return result

def split_amount(total_paise: int, participants: list[dict], method: str):
    if not participants:
        raise ValueError("Select at least one participant.")
    ids = [p["member_id"] for p in participants]
    if len(ids) != len(set(ids)):
        raise ValueError("Participants cannot be duplicated.")
    if method == "equal":
        weights = [1] * len(participants)
    elif method == "shares":
        weights = [float(p["value"]) for p in participants]
        if any(w <= 0 for w in weights): raise ValueError("Share weights must be positive.")
    elif method == "percentage":
        weights = [float(p["value"]) for p in participants]
        if any(w < 0 for w in weights) or abs(sum(weights) - 100) > 0.01:
            raise ValueError("Percentages must add up to 100.")
    elif method == "exact":
        amounts = [paise(float(p["value"])) for p in participants]
        if any(a < 0 for a in amounts) or sum(amounts) != total_paise:
            raise ValueError("Exact shares must add up to the expense total.")
        return dict(zip(ids, amounts))
    else:
        raise ValueError("Unsupported split method.")
    denominator = sum(weights)
    if denominator <= 0: raise ValueError("Split weights must sum to a positive number.")
    raw = [total_paise * w / denominator for w in weights]
    rounded = [int(x) for x in raw]
    remainder = total_paise - sum(rounded)
    # Distribute leftover paise deterministically to largest fractional remainders.
    order = sorted(range(len(raw)), key=lambda i: (raw[i] - rounded[i]), reverse=True)
    for i in order[:remainder]:
        rounded[i] += 1
    return dict(zip(ids, rounded))
