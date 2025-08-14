from etrade_api.api_connection import ETradeAPIConnection
from utils.logging import get_logger
from typing import Optional, Dict, Any, List

logger = get_logger(__name__)


class MarketData:
    """
    Handles fetching various types of market data from the E*Trade API.
    """

    def __init__(self, api_connection: ETradeAPIConnection):
        """
        Initializes MarketData with an ETradeAPIConnection instance.
        """
        self.api_connection = api_connection
        self.base_url = "https://apisb.etrade.com/v1"

    def _make_api_call(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Helper method to make authenticated GET requests to the E*Trade API."""
        try:
            session = self.api_connection.get_session()
            url = f"{self.base_url}/{endpoint}"
            response = session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"E*Trade API Market Data Error for {endpoint}: {e}")
            return None

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches real-time quote data for a given stock symbol.

        Args:
            symbol (str): The stock ticker symbol (e.g., "AAPL").

        Returns:
            dict: A dictionary containing quote data (e.g., last price, volume, change).
                  Returns None if data cannot be fetched or on error.
        """
        endpoint = "market/quote/" + symbol + ".json"
        params = {"detailFlag": "ALL"}
        data = self._make_api_call(endpoint, params)

        if data and "QuoteResponse" in data and "QuoteData" in data["QuoteResponse"]:
            if data["QuoteResponse"]["QuoteData"]:
                quote_data = data["QuoteResponse"]["QuoteData"][0]
                return {
                    "symbol": quote_data.get("product", {}).get("symbol"),
                    "lastPrice": quote_data.get("All", {}).get("lastTrade"),
                    "changePct": quote_data.get("All", {}).get("changeClosePercentage"),
                    "volume": quote_data.get("All", {}).get("totalVolume"),
                    "bid": quote_data.get("All", {}).get("bid"),
                    "ask": quote_data.get("All", {}).get("ask"),
                    "high": quote_data.get("All", {}).get("high"),
                    "low": quote_data.get("All", {}).get("low"),
                    "open": quote_data.get("All", {}).get("open"),
                    "close": quote_data.get("All", {}).get("previousClose"),
                }
        logger.warning(f"Failed to get quote for {symbol}.")
        return None

    def get_historical_data(
        self, symbol: str, interval: str = "1day", period: str = "3months"
    ) -> List[Dict[str, Any]]:
        logger.warning(
            f"Historical data endpoint may be non-functional in the E*Trade sandbox. Returning no data for {symbol}."
        )
        return []

    def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        logger.warning(
            f"News/sentiment data endpoint may be non-functional in the E*Trade sandbox. Returning no data for {symbol}."
        )
        return {
            "earningsNews": "Not available from E*Trade API directly as 'earnings news' field.",
            "marketSentiment": "General market sentiment not directly provided by E*Trade news API.",
            "analystRatings": "Analyst ratings not directly provided by E*Trade news API.",
        }
