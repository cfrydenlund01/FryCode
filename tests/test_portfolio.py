import json
from user_data.portfolio import Portfolio


def test_load_portfolio_reloads(tmp_path, caplog):
    tmp_file = tmp_path / "portfolio.json"
    initial = {"AAPL": {"quantity": 1, "costBasis": 100}}
    updated = {"AAPL": {"quantity": 2, "costBasis": 200}}

    with open(tmp_file, "w") as f:
        json.dump(initial, f)

    p = Portfolio()
    p.portfolio_file = str(tmp_file)
    with caplog.at_level("INFO"):
        p.load_portfolio()
    assert p.get_holdings() == initial
    assert "Portfolio reloaded from file." in caplog.text

    with open(tmp_file, "w") as f:
        json.dump(updated, f)

    caplog.clear()
    with caplog.at_level("INFO"):
        p.load_portfolio()
    assert p.get_holdings() == updated
    assert "Portfolio reloaded from file." in caplog.text
