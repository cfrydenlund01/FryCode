import json
from user_data.portfolio import Portfolio


def test_load_portfolio_reloads(tmp_path):
    tmp_file = tmp_path / "portfolio.json"
    initial = {"AAPL": {"quantity": 1, "costBasis": 100}}
    updated = {"AAPL": {"quantity": 2, "costBasis": 200}}

    with open(tmp_file, "w") as f:
        json.dump(initial, f)

    p = Portfolio()
    p.portfolio_file = str(tmp_file)
    p.load_portfolio()
    assert p.get_holdings() == initial

    with open(tmp_file, "w") as f:
        json.dump(updated, f)

    p.load_portfolio()
    assert p.get_holdings() == updated

