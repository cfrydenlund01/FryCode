# etrade_api/api_connection.py

import webbrowser
from datetime import datetime, timezone
from typing import Optional

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

    def __init__(self):
        self.consumer_key, self.consumer_secret = credentials.get_consumer_credentials()
        self.account_id: Optional[str] = None

        self.oauth = None
        self.access_token = None
        self.access_token_secret = None
        self.token_manager = TokenManager()

        if not self.consumer_key or not self.consumer_secret:
            raise ETradeCredentialsMissing(
                "E*TRADE credentials not available in Windows Credential Manager."
            )

        self._load_tokens()

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
        # Using sandbox URLs for development as per standard practice
        request_token_url = "https://apisb.etrade.com/oauth/request_token"
        authorize_url = "https://apisb.etrade.com/oauth/authorize"
        access_token_url = "https://apisb.etrade.com/oauth/access_token"

        # Step 1: Get a Request Token
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

        # Step 2: Authorize the Request Token
        authorization_url = self.oauth.authorization_url(authorize_url)

        # Open the authorization URL in the user's default web browser
        webbrowser.open_new_tab(authorization_url)
        logger.info(
            f"Please open this URL in your browser to authorize E*Trade: {authorization_url}"
        )

        # Prompt the user to enter the verification code from the browser
        print("\n--- E*Trade API Authentication ---")
        print("A browser window has been opened for you to authorize this application.")
        print(
            "Please copy the verification code from the browser page and paste it below."
        )
        oauth_verifier = input("Enter the verification code: ").strip()

        # Step 3: Get the Access Token
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

            # Fetch and set the user's default account ID for trading
            self._fetch_and_set_account_id()

            self._save_tokens()
            return True
        except Exception as e:
            logger.error(f"Failed to get E*Trade Access Token: {e}")
            return False

    def _fetch_and_set_account_id(self):
        """
        Fetches the user's primary account ID from E*Trade and sets it.
        This is a required step for placing orders.
        """
        if not self.is_authenticated():
            logger.warning("Not authenticated to fetch account ID.")
            return

        try:
            # E*Trade has a dedicated endpoint for listing accounts
            accounts_url = "https://apisb.etrade.com/v1/accounts/list.json"
            response = self.oauth.get(accounts_url)
            response.raise_for_status()
            accounts_data = response.json()

            # The API response structure can be complex. We need to navigate it carefully.
            accounts_list = (
                accounts_data.get("AccountListResponse", {})
                .get("Accounts", {})
                .get("Account", [])
            )

            if accounts_list:
                # Use the first account found as the default for this application
                self.account_id = accounts_list[0].get("accountId")
                logger.info(f"Fetched E*Trade default Account ID: {self.account_id}")
            else:
                logger.warning("No E*Trade accounts found for the authenticated user.")
        except Exception as e:
            logger.error(f"Error fetching E*Trade Account ID: {e}")

    def is_authenticated(self):
        """
        Checks if the OAuth session has an access token, indicating authentication.
        """
        return (
            self.oauth is not None
            and self.access_token is not None
            and self.access_token_secret is not None
        )

    def get_session(self):
        """
        Returns the authenticated OAuth1Session object.
        """
        if not self.is_authenticated():
            logger.warning(
                "E*Trade API not authenticated. Attempting to re-authenticate."
            )
            if not self.get_access_token():
                raise
        else:
            try:
                self.token_manager.ensure_active()
            except ETradeCredentialsMissing:
                logger.warning("E*Trade token expired. Re-authenticating.")
                if not self.get_access_token():
                    raise
        return self.oauth