from datetime import datetime, timedelta, timezone

import pytest

from etrade_api import token_manager
from etrade_api.exceptions import ETradeCredentialsMissing
from utils import credentials


class DummyResp:
    def raise_for_status(self):
        pass


class DummySession:
    def __init__(self, *a, **k):
        pass

    def get(self, url):
        return DummyResp()


def test_renew_on_idle(monkeypatch, fake_keyring):
    credentials.set_consumer_credentials("ck", "cs")
    issued = (datetime.now(timezone.utc) - timedelta(minutes=100)).isoformat()
    credentials.set_access_token("tok", "sec", issued)
    monkeypatch.setattr(token_manager, "OAuth1Session", DummySession)
    tm = token_manager.TokenManager()
    tok, sec = tm.ensure_active()
    assert tok == "tok" and sec == "sec"
    _, _, issued_after = credentials.get_access_token()
    assert issued_after and (datetime.now(timezone.utc) - issued_after) < timedelta(minutes=5)


def test_midnight_expiry(fake_keyring):
    credentials.set_consumer_credentials("ck", "cs")
    yesterday = (datetime.now(token_manager.EASTERN) - timedelta(days=1)).astimezone(
        timezone.utc
    )
    credentials.set_access_token("tok", "sec", yesterday.isoformat())
    tm = token_manager.TokenManager()
    with pytest.raises(ETradeCredentialsMissing):
        tm.ensure_active()

