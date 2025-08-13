"""Handle renewal and expiry of E*TRADE access tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from requests_oauthlib import OAuth1Session

from etrade_api.exceptions import ETradeCredentialsMissing
from utils import credentials
from utils.credentials import EASTERN


class TokenManager:
    """Maintain a valid E*TRADE access token."""

    def __init__(self, sandbox: bool = True):
        self.base = "https://apisb.etrade.com" if sandbox else "https://api.etrade.com"
        self.last_used: datetime | None = None

    def ensure_active(self) -> tuple[str, str]:
        """Return active token pair, renewing if idle."""
        consumer_key, consumer_secret = credentials.get_consumer_credentials()
        token, token_secret, issued = credentials.get_access_token()
        if not (consumer_key and consumer_secret and token and token_secret and issued):
            raise ETradeCredentialsMissing("Missing E*TRADE credentials or token.")

        now = datetime.now(timezone.utc)
        if issued.astimezone(EASTERN).date() != now.astimezone(EASTERN).date():
            raise ETradeCredentialsMissing("E*TRADE token expired at midnight Eastern.")

        idle_anchor = self.last_used or issued
        if now - idle_anchor > timedelta(minutes=90):
            oauth = OAuth1Session(
                consumer_key,
                client_secret=consumer_secret,
                resource_owner_key=token,
                resource_owner_secret=token_secret,
            )
            url = f"{self.base}/oauth/renew_access_token"
            resp = oauth.get(url)
            resp.raise_for_status()
            credentials.set_access_token(token, token_secret, now.isoformat())
        self.last_used = now
        return token, token_secret