# etrade_api/api_connection.py

import os
import subprocess
import json
import webbrowser
import logging
import sys
from requests_oauthlib import OAuth1Session
from utils.logging import get_logger

logger = get_logger(__name__)

class ETradeAPIConnection:
    """
    Manages OAuth authentication and session for the E*Trade API.
    Retrieves consumer key and secret from the Windows SecretManagement vault via PowerShell
    for enhanced security.
    """
    def __init__(self):
        """
        Initializes ETradeAPIConnection by retrieving credentials from the secure vault
        and setting up the session.
        """
        # Retrieve credentials from the secure Windows SecretManagement vault
        self.consumer_key = self._get_secret("ETrade-ConsumerKey")
        self.consumer_secret = self._get_secret("ETrade-ConsumerSecret")
        # E*Trade API provides an account list endpoint, so we can fetch this dynamically.
        # However, for specific use cases, a hardcoded account ID can still be stored.
        self.account_id = None 

        self.oauth = None
        self.access_token = None
        self.access_token_secret = None
        self.token_file = "user_data/etrade_tokens.json"

        if not self.consumer_key or not self.consumer_secret:
            logger.critical("E*TRADE API credentials could not be retrieved from the secure vault. "
                            "Please ensure PowerShell SecretManagement is configured correctly.")
            raise ValueError("E*TRADE API credentials are not set or not accessible.")
        
        self._load_tokens() # Attempt to load previously saved tokens

    def _get_secret(self, secret_name: str) -> str:
        """Retrieve a secret value.

        On Windows, this attempts to pull the secret from the PowerShell
        SecretManagement vault. If retrieval fails or on non-Windows systems,
        the method falls back to environment variables using a conventional
        upper-case name (e.g. ``ETrade-ConsumerKey`` -> ``ETRADE_CONSUMER_KEY``).
        """
        # Fallback to environment variables first (works cross-platform)
        env_name = secret_name.replace("-", "_").upper()
        env_val = os.getenv(env_name)
        if env_val:
            return env_val

        # Only attempt PowerShell retrieval on Windows
        if not sys.platform.startswith("win"):
            logger.warning(
                "PowerShell secret retrieval is only supported on Windows. "
                f"Environment variable '{env_name}' not set."
            )
            return None

        try:
            ps_command = f"""
            $secret = Get-Secret -Name \"{secret_name}\" -AsPlainText
            Write-Host $secret
            """

            result = subprocess.run(
                ["powershell.exe", "-Command", ps_command],
                capture_output=True,
                text=True,
                check=True,
                shell=False,
            )

            secret = result.stdout.strip()
            if not secret:
                logger.warning(
                    f"PowerShell returned an empty string for secret '{secret_name}'."
                )
            return secret
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to retrieve secret '{secret_name}' from PowerShell."
            )
            logger.error(f"PowerShell Error Output: {e.stderr}")
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while retrieving secret '{secret_name}': {e}"
            )
            return None

    def _load_tokens(self):
        """
        Loads access tokens from a local file if they exist.
        """
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.access_token_secret = tokens.get('access_token_secret')
                    self.account_id = tokens.get('account_id')
                    logger.info("E*Trade access tokens loaded from file.")
            except Exception as e:
                logger.error(f"Error loading E*Trade tokens from file: {e}")
                self.access_token = None
                self.access_token_secret = None
                self.account_id = None
        else:
            logger.info("No saved E*Trade access tokens found.")

    def _save_tokens(self):
        """
        Saves access tokens and account ID to a local file.
        """
        tokens = {
            'access_token': self.access_token,
            'access_token_secret': self.access_token_secret,
            'account_id': self.account_id
        }
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f, indent=4)
        logger.info("E*Trade access tokens saved to file.")

    def get_access_token(self):
        """
        Performs the OAuth 1.0a flow to get an access token.
        If tokens are already loaded, it verifies them.
        """
        if self.access_token and self.access_token_secret:
            # Create a session with the saved tokens
            self.oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_token_secret
            )
            logger.info("Using existing E*Trade access token.")
            # For a more robust check, we could make a light API call here
            # to ensure the token is still valid.
            return True

        return self._perform_oauth_flow()

    def _perform_oauth_flow(self):
        """
        Executes the full OAuth 1.0a authentication flow, including opening a browser
        for user authorization.
        """
        request_token_url = "https://api.etrade.com/oauth/request_token"
        authorize_url = "https://us.etrade.com/oauth/authorize"
        access_token_url = "https://api.etrade.com/oauth/access_token"

        # Step 1: Get a Request Token
        self.oauth = OAuth1Session(self.consumer_key, client_secret=self.consumer_secret, callback_uri="oob")
        try:
            fetch_response = self.oauth.fetch_request_token(request_token_url)
            resource_owner_key = fetch_response.get('oauth_token')
            resource_owner_secret = fetch_response.get('oauth_token_secret')
            logger.info("E*Trade Request Token obtained.")
        except Exception as e:
            logger.error(f"Failed to get E*Trade Request Token: {e}")
            return False

        # Step 2: Authorize the Request Token
        authorization_url = self.oauth.authorization_url(authorize_url)
        
        # Open the authorization URL in the user's default web browser
        webbrowser.open_new_tab(authorization_url)
        logger.info(f"Please open this URL in your browser to authorize E*Trade: {authorization_url}")

        # Prompt the user to enter the verification code from the browser
        print("\n--- E*Trade API Authentication ---")
        print("A browser window has been opened for you to authorize this application.")
        print("Please copy the verification code from the browser page and paste it below.")
        oauth_verifier = input("Enter the verification code: ").strip()

        # Step 3: Get the Access Token
        try:
            self.oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret,
                verifier=oauth_verifier
            )
            access_token_response = self.oauth.fetch_access_token(access_token_url)
            self.access_token = access_token_response.get('oauth_token')
            self.access_token_secret = access_token_response.get('oauth_token_secret')
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
            accounts_url = "https://api.etrade.com/v1/accounts/list.json"
            response = self.oauth.get(accounts_url)
            response.raise_for_status()
            accounts_data = response.json()
            
            # The API response structure can be complex. We need to navigate it carefully.
            accounts_list = accounts_data.get('AccountListResponse', {}).get('Accounts', {}).get('Account', [])
            
            if accounts_list:
                # Use the first account found as the default for this application
                self.account_id = accounts_list[0].get('accountId')
                logger.info(f"Fetched E*Trade default Account ID: {self.account_id}")
            else:
                logger.warning("No E*Trade accounts found for the authenticated user.")
        except Exception as e:
            logger.error(f"Error fetching E*Trade Account ID: {e}")

    def is_authenticated(self):
        """
        Checks if the OAuth session has an access token, indicating authentication.
        """
        return self.oauth is not None and self.access_token is not None and self.access_token_secret is not None

    def get_session(self):
        """
        Returns the authenticated OAuth1Session object.
        """
        if not self.is_authenticated():
            logger.warning("E*Trade API not authenticated. Attempting to re-authenticate.")
            if not self.get_access_token():
                raise Exception("E*Trade API not authenticated.")
        return self.oauth