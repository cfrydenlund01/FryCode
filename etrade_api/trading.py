from etrade_api.api_connection import ETradeAPIConnection
from utils.logging import get_logger
from typing import Optional, Dict, Any, List

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
        self.base_url = "https://apisb.etrade.com/v1"

    def _make_api_call(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Helper to make authenticated GET requests to the E*Trade API."""
        try:
            session = self.api_connection.get_session()
            url = f"{self.base_url}/{endpoint}"
            response = session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"E*Trade API Trading GET Error for {endpoint}: {e}")
            return None

    def _make_api_post_call(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
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
            logger.error(f"E*Trade API Trading POST Error for {endpoint}: {e}")
            return None

    def place_order(
        self,
        account_id: str,
        symbol: str,
        action: str,
        quantity: int,
        order_type: str = "MARKET",
    ) -> Optional[Dict[str, Any]]:
        """
        Places a trade order (Buy/Sell) through the E*Trade API.
        """
        if not account_id:
            logger.error("Account ID is required to place an E*Trade order.")
            return None

        payload = {
            "PlaceOrderRequest": {
                "Order": [
                    {
                        "allOrNone": False,
                        "priceType": order_type.upper(),
                        "orderTerm": "GOOD_FOR_DAY",
                        "marketSession": "REGULAR",
                        "Instrument": [
                            {
                                "Product": {"securityType": "EQ", "symbol": symbol},
                                "orderAction": action.upper(),
                                "quantityType": "QUANTITY",
                                "quantity": quantity,
                            }
                        ],
                    }
                ]
            }
        }

        endpoint = f"accounts/{account_id}/orders/place.json"
        logger.info(
            f"Attempting to place {action} order for {quantity} {symbol} on E*Trade (Account: {account_id})."
        )

        preview_endpoint = f"accounts/{account_id}/orders/preview.json"
        preview_response = self._make_api_post_call(preview_endpoint, payload)

        if (
            preview_response
            and "PreviewOrderResponse" in preview_response
            and "Order" in preview_response["PreviewOrderResponse"]
        ):
            logger.info(
                f"Order preview successful for {symbol}. Proceeding to place order."
            )
            client_order_id = preview_response["PreviewOrderResponse"].get(
                "clientOrderId"
            )
            place_payload = {
                "PlaceOrderRequest": {
                    "Order": preview_response["PreviewOrderResponse"]["Order"],
                    "clientOrderId": client_order_id,
                    "PreviewIds": [
                        preview_response["PreviewOrderResponse"]["PreviewIds"][0][
                            "previewId"
                        ]
                    ],
                }
            }
            return self._make_api_post_call(endpoint, place_payload)
        else:
            logger.error(
                f"Failed to preview order for {symbol}. Response: {preview_response}"
            )
            return None

    def get_portfolio(self, account_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches the current portfolio holdings for a given account.
        """
        if not account_id:
            logger.error("Account ID is required to fetch E*Trade portfolio.")
            return None

        endpoint = f"accounts/{account_id}/portfolio.json"
        data = self._make_api_call(endpoint)

        portfolio_holdings = []
        if (
            data
            and "PortfolioResponse" in data
            and "AccountPortfolio" in data["PortfolioResponse"]
        ):
            account_portfolio_list = data["PortfolioResponse"]["AccountPortfolio"]
            for account_portfolio in account_portfolio_list:
                if "Position" in account_portfolio:
                    for position in account_portfolio["Position"]:
                        portfolio_holdings.append(
                            {
                                "symbol": position.get("Product", {}).get("symbol"),
                                "quantity": position.get("quantity"),
                                "costBasis": position.get("costBasis"),
                                "marketValue": position.get("marketValue"),
                            }
                        )
            logger.info(f"Fetched portfolio for account {account_id}.")
        else:
            logger.warning(f"No portfolio data received for account {account_id}.")
        return portfolio_holdings
