# etrade_api/api_connection.py

import webbrowser
from datetime import datetime, timezone
from typing import Optional, Callable

from requests_oauthlib import OAuth1Session

from etrade_api.exceptions import ETradeCredentialsMissing
from etrade_api.token_manager import TokenManager
from utils import credentials
from utils.logging import get_logger

logger = get_logger(__name__)


class ETradeAPIConnection:
    """
    Manages OAuth authentication and session for the E*Trade API.
    """

    def __init__(self, get_verifier_callback: Callable[[], str]):
        self.consumer_key, self.consumer_secret = credentials.get_consumer_credentials()
        self.account_id: Optional[str] = None
        self.get_verifier_callback = get_verifier_callback

        self.oauth = None
        self.access_token = None
        self.access_token_secret = None
        self.token_manager = TokenManager(sandbox=True)

        if not self.consumer_key or not self.consumer_secret:
            raise ETradeCredentialsMissing(
                "E*TRADE credentials not available in Windows Credential Manager."
            )

        self._load_tokens()

        if not self.is_authenticated():
            self.get_access_token()

    def _load_tokens(self):
        """Loads access tokens from the credential store if they exist."""
        token, secret, _issued = credentials.get_access_token()
        if token and secret:
            self.access_token = token
            self.access_token_secret = secret
            logger.info("E*Trade access tokens loaded from credential store.")
        else:
            logger.info("No saved E*Trade access tokens found.")

    def _save_tokens(self):
        """Saves access tokens to the credential store."""
        if self.access_token and self.access_token_secret:
            credentials.set_access_token(
                self.access_token,
                self.access_token_secret,
                datetime.now(timezone.utc).isoformat(),
            )
            logger.info("E*Trade access tokens saved to credential store.")

    def get_access_token(self):
        """
        Performs the OAuth 1.0a flow to get an access token.
        If tokens are already loaded, it verifies them.
        """
        if self.access_token and self.access_token_secret:
            self.oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_token_secret,
            )
            logger.info("Using existing E*Trade access token.")
            return True

        return self._perform_oauth_flow()

    def _perform_oauth_flow(self):
        """
        Executes the full OAuth 1.0a authentication flow, including opening a browser
        for user authorization.
        """
        request_token_url = "https://apisb.etrade.com/oauth/request_token"
        authorize_url_base = "https://us.etrade.com/e/t/etws/authorize"
        access_token_url = "https://apisb.etrade.com/oauth/access_token"

        self.oauth = OAuth1Session(
            self.consumer_key, client_secret=self.consumer_secret, callback_uri="oob"
        )
        try:
            fetch_response = self.oauth.fetch_request_token(request_token_url)
            resource_owner_key = fetch_response.get("oauth_token")
            resource_owner_secret = fetch_response.get("oauth_token_secret")
            logger.info("E*Trade Request Token obtained.")
        except Exception as e:
            logger.error(f"Failed to get E*Trade Request Token: {e}")
            return False

        authorization_url = (
            f"{authorize_url_base}?key={self.consumer_key}&token={resource_owner_key}"
        )
        webbrowser.open_new_tab(authorization_url)
        logger.info(
            f"Please open this URL in your browser to authorize E*Trade: {authorization_url}"
        )

        oauth_verifier = self.get_verifier_callback()

        if not oauth_verifier:
            logger.warning(
                "User cancelled E*Trade authentication or did not provide a verifier."
            )
            return False

        try:
            self.oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret,
                verifier=oauth_verifier,
            )
            access_token_response = self.oauth.fetch_access_token(access_token_url)
            self.access_token = access_token_response.get("oauth_token")
            self.access_token_secret = access_token_response.get("oauth_token_secret")
            logger.info("E*Trade Access Token obtained successfully.")
            self._fetch_and_set_account_id()
            self._save_tokens()
            return True
        except Exception as e:
            logger.error(f"Failed to get E*Trade Access Token: {e}")
            return False

    def _fetch_and_set_account_id(self):
        if not self.is_authenticated():
            logger.warning("Not authenticated to fetch account ID.")
            return

        try:
            accounts_url = "https://apisb.etrade.com/v1/accounts/list.json"
            response = self.oauth.get(accounts_url)
            response.raise_for_status()
            accounts_data = response.json()

            accounts_list = (
                accounts_data.get("AccountListResponse", {})
                .get("Accounts", {})
                .get("Account", [])
            )

            if accounts_list:
                self.account_id = accounts_list[0].get("accountId")
                logger.info(f"Fetched E*Trade default Account ID: {self.account_id}")
            else:
                logger.warning("No E*Trade accounts found for the authenticated user.")
        except Exception as e:
            logger.error(f"Error fetching E*Trade Account ID: {e}")

    def is_authenticated(self):
        return (
            self.oauth is not None
            and self.access_token is not None
            and self.access_token_secret is not None
        )

    def get_session(self):
        if not self.is_authenticated():
            logger.warning(
                "E*Trade API not authenticated. Attempting to re-authenticate."
            )
            if not self.get_access_token():
                raise Exception("E*Trade API not authenticated.")
        else:
            try:
                self.token_manager.ensure_active()
            except ETradeCredentialsMissing:
                logger.warning("E*Trade token expired. Re-authenticating.")
                if not self.get_access_token():
                    raise Exception("E*Trade API not authenticated.")
        return self.oauth
