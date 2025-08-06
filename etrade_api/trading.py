from etrade_api.api_connection import ETradeAPIConnection
from utils.logging import get_logger

logger = get_logger(__name__)

class Trading:
    """
    Handles placing and managing trade orders through the E*Trade API.
    """
    def __init__(self, api_connection: ETradeAPIConnection):
        """
        Initializes Trading with an ETradeAPIConnection instance.
        """
        self.api_connection = api_connection
        self.base_url = "https://api.etrade.com/v1" # Base URL for E*Trade API

    def _make_api_post_call(self, endpoint, payload):
        """
        Helper method to make authenticated POST requests to the E*Trade API.
        """
        try:
            session = self.api_connection.get_session()
            url = f"{self.base_url}/{endpoint}"
            headers = {"Content-Type": "application/json"}
            response = session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"E*Trade API Trading Error for {endpoint}: {e}")
            return None

    def place_order(self, account_id: str, symbol: str, action: str, quantity: int, order_type: str = "MARKET") -> dict:
        """
        Places a trade order (Buy/Sell) through the E*Trade API.

        Args:
            account_id (str): The E*Trade account ID to place the order from.
            symbol (str): The stock ticker symbol.
            action (str): "BUY" or "SELL".
            quantity (int): The number of shares.
            order_type (str): "MARKET", "LIMIT", "STOP", etc. (E*Trade specific).

        Returns:
            dict: The API response after placing the order, including order ID.
                  Returns None on failure.
        """
        if not account_id:
            logger.error("Account ID is required to place an E*Trade order.")
            return None

        # E*Trade API expects a specific JSON structure for placing orders.
        # This structure needs to be precisely matched with E*Trade's documentation.
        # Example structure (highly simplified, refer to E*Trade documentation):
        payload = {
            "PlaceOrderRequest": {
                "Order": [
                    {
                        "allOrNone": False,
                        "priceType": order_type.upper(),
                        "orderTerm": "GOOD_FOR_DAY", # Or "GOOD_UNTIL_CANCEL" etc.
                        "marketSession": "REGULAR", # Or "EXTENDED"
                        "Instrument": [
                            {
                                "Product": {
                                    "securityType": "EQ", # Equity
                                    "symbol": symbol
                                },
                                "orderAction": action.upper(),
                                "quantityType": "QUANTITY",
                                "quantity": quantity
                            }
                        ]
                    }
                ]
            }
        }

        endpoint = f"accounts/{account_id}/orders/place.json" # Endpoint for placing orders
        logger.info(f"Attempting to place {action} order for {quantity} {symbol} on E*Trade (Account: {account_id}).")
        # First, send a 'preview' order request (E*Trade best practice)
        preview_endpoint = f"accounts/{account_id}/orders/preview.json"
        preview_response = self._make_api_post_call(preview_endpoint, payload)

        if preview_response and 'PreviewOrderResponse' in preview_response and 'Order' in preview_response['PreviewOrderResponse']:
            logger.info(f"Order preview successful for {symbol}. Proceeding to place order.")
            # E*Trade requires the clientOrderId and other details from the preview response
            # to be sent back in the actual place order request.
            preview_order_data = preview_response['PreviewOrderResponse']['Order'][0]
            client_order_id = preview_response['PreviewOrderResponse'].get('clientOrderId')
            # The actual payload for 'place' often needs to include the 'Order' object returned by 'preview'
            # (or at least its unique identifiers like clientOrderId and orderId if available).
            # This part is critical and *highly* dependent on E*Trade's exact API spec.
            # For simplicity, we'll resend a similar payload, but real implementation needs careful handling
            # of `previewId` or other identifiers from the preview response.
            place_payload = {
                "PlaceOrderRequest": {
                    "Order": preview_response['PreviewOrderResponse']['Order'], # Send the whole Order array back
                    "clientOrderId": client_order_id, # Crucial for E*Trade
                    "PreviewIds": [preview_response['PreviewOrderResponse']['PreviewIds'][0]['previewId']] # If E*Trade uses this
                }
            }
            return self._make_api_post_call(endpoint, place_payload)
        else:
            logger.error(f"Failed to preview order for {symbol}. Response: {preview_response}")
            return None

    def get_portfolio(self, account_id: str) -> list:
        """
        Fetches the current portfolio holdings for a given account.

        Args:
            account_id (str): The E*Trade account ID.

        Returns:
            list: A list of dictionaries, each representing a position.
                  Returns an empty list on failure.
        """
        if not account_id:
            logger.error("Account ID is required to fetch E*Trade portfolio.")
            return []

        # Endpoint for portfolio holdings
        endpoint = f"accounts/{account_id}/portfolio.json"
        data = self._make_api_call(endpoint) # Using _make_api_call as it's a GET request

        portfolio_holdings = []
        if data and 'PortfolioResponse' in data and 'AccountPortfolio' in data['PortfolioResponse']:
            account_portfolio_list = data['PortfolioResponse']['AccountPortfolio']
            for account_portfolio in account_portfolio_list:
                if 'Position' in account_portfolio:
                    for position in account_portfolio['Position']:
                        portfolio_holdings.append({
                            "symbol": position.get('Product', {}).get('symbol'),
                            "quantity": position.get('quantity'),
                            "costBasis": position.get('costBasis'),
                            "marketValue": position.get('marketValue')
                        })
            logger.info(f"Fetched portfolio for account {account_id}.")
        else:
            logger.warning(f"No portfolio data received for account {account_id}.")
        return portfolio_holdings