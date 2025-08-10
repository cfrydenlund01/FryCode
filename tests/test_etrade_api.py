import pytest
from etrade_api.api_connection import ETradeAPIConnection


def test_missing_creds(monkeypatch):
    monkeypatch.delenv("ETRADE_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("ETRADE_CONSUMER_SECRET", raising=False)
    with pytest.raises(ValueError):
        ETradeAPIConnection()


def test_init_with_env(monkeypatch):
    monkeypatch.setenv("ETRADE_CONSUMER_KEY", "key")
    monkeypatch.setenv("ETRADE_CONSUMER_SECRET", "secret")
    monkeypatch.setenv("ETRADE_ACCOUNT_ID", "123")
    conn = ETradeAPIConnection()
    assert conn.consumer_key == "key"
    assert conn.account_id == "123"


def test_get_access_token_uses_existing(monkeypatch):
    monkeypatch.setenv("ETRADE_CONSUMER_KEY", "key")
    monkeypatch.setenv("ETRADE_CONSUMER_SECRET", "secret")
    conn = ETradeAPIConnection()
    conn.access_token = "tok"
    conn.access_token_secret = "sec"

    def fake_session(*_a, **_k):
        return "session"

    monkeypatch.setattr("etrade_api.api_connection.OAuth1Session", fake_session)
    assert conn.get_access_token() is True
    assert conn.oauth == "session"
