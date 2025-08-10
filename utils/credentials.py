"""Credential storage using Windows Credential Manager via keyring."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

import keyring
from zoneinfo import ZoneInfo

SERVICE = "FryCode:ETrade"
CONSUMER_KEY = "consumer_key"
CONSUMER_SECRET = "consumer_secret"
ACCESS_TOKEN = "access_token"
ACCESS_TOKEN_SECRET = "access_token_secret"
TOKEN_ISSUED = "token_issued"

EASTERN = ZoneInfo("America/New_York")


def set_consumer_credentials(key: str, secret: str) -> None:
    keyring.set_password(SERVICE, CONSUMER_KEY, key)
    keyring.set_password(SERVICE, CONSUMER_SECRET, secret)


def get_consumer_credentials() -> Tuple[Optional[str], Optional[str]]:
    key = keyring.get_password(SERVICE, CONSUMER_KEY)
    secret = keyring.get_password(SERVICE, CONSUMER_SECRET)
    return key, secret


def have_consumer_credentials() -> bool:
    key, secret = get_consumer_credentials()
    return bool(key and secret)


def set_access_token(token: str, token_secret: str, issued_utc_iso: str) -> None:
    keyring.set_password(SERVICE, ACCESS_TOKEN, token)
    keyring.set_password(SERVICE, ACCESS_TOKEN_SECRET, token_secret)
    keyring.set_password(SERVICE, TOKEN_ISSUED, issued_utc_iso)


def get_access_token() -> Tuple[Optional[str], Optional[str], Optional[datetime]]:
    token = keyring.get_password(SERVICE, ACCESS_TOKEN)
    secret = keyring.get_password(SERVICE, ACCESS_TOKEN_SECRET)
    issued_iso = keyring.get_password(SERVICE, TOKEN_ISSUED)
    if not token or not secret or not issued_iso:
        return None, None, None
    try:
        issued = datetime.fromisoformat(issued_iso)
        if issued.tzinfo is None:
            issued = issued.replace(tzinfo=timezone.utc)
    except Exception:
        issued = None
    return token, secret, issued


def clear_all_credentials() -> None:
    for name in [
        CONSUMER_KEY,
        CONSUMER_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET,
        TOKEN_ISSUED,
    ]:
        try:
            keyring.delete_password(SERVICE, name)
        except Exception:
            pass

