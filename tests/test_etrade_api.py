import pytest
import pytest

from etrade_api.api_connection import ETradeAPIConnection
from etrade_api.exceptions import ETradeCredentialsMissing
from utils import credentials


def test_missing_creds(fake_keyring):
    with pytest.raises(ETradeCredentialsMissing):
        ETradeAPIConnection()


def test_init_with_creds(fake_keyring):
    credentials.set_consumer_credentials("key", "secret")
    conn = ETradeAPIConnection()
    assert conn.consumer_key == "key"


def test_get_access_token_uses_existing(monkeypatch, fake_keyring):
    credentials.set_consumer_credentials("key", "secret")
    credentials.set_access_token("tok", "sec", "2024-01-01T00:00:00+00:00")
    conn = ETradeAPIConnection()

    monkeypatch.setattr(
        "etrade_api.api_connection.OAuth1Session", lambda *a, **k: "session"
    )
    assert conn.get_access_token() is True
    assert conn.oauth == "session"
