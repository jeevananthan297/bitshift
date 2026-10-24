from app.services import split_amount, simplify

def test_equal_split_remainder():
    shares = split_amount(100, [{"member_id":1,"value":1},{"member_id":2,"value":1},{"member_id":3,"value":1}], "equal")
    assert sum(shares.values()) == 100
    assert sorted(shares.values()) == [33, 33, 34]

def test_exact_split():
    shares = split_amount(1000, [{"member_id":1,"value":4},{"member_id":2,"value":6}], "exact")
    assert shares == {1:400, 2:600}

def test_percentage_split():
    shares = split_amount(1000, [{"member_id":1,"value":25},{"member_id":2,"value":75}], "percentage")
    assert shares == {1:250, 2:750}

def test_weighted_split():
    shares = split_amount(1000, [{"member_id":1,"value":1},{"member_id":2,"value":3}], "shares")
    assert shares == {1:250, 2:750}

def test_debt_simplification():
    balances = [
        {"member_id":1,"name":"Alice","balance_paise":50000},
        {"member_id":2,"name":"Bob","balance_paise":-10000},
        {"member_id":3,"name":"Charlie","balance_paise":-40000},
    ]
    plan = simplify(balances)
    assert sum(x["amount_paise"] for x in plan) == 50000
    assert {(x["payer_name"],x["receiver_name"],x["amount_paise"]) for x in plan} == {("Bob","Alice",10000),("Charlie","Alice",40000)}
