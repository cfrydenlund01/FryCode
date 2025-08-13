from etrade_api.api_connection import ETradeAPIConnection
from utils.logging import get_logger

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
        # Use the E*Trade sandbox environment by default
        self.base_url = "https://apisb.etrade.com/v1"

    def _make_api_call(self, endpoint, params=None):
        """
        Helper method to make authenticated GET requests to the E*Trade API.
        """
        try:
            session = self.api_connection.get_session()
            url = f"{self.base_url}/{endpoint}"
            response = session.get(url, params=params)
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except Exception as e:
            logger.error(f"E*Trade API Market Data Error for {endpoint}: {e}")
            return None

    def get_quote(self, symbol: str) -> dict:
        """
        Fetches real-time quote data for a given stock symbol.

        Args:
            symbol (str): The stock ticker symbol (e.g., "AAPL").

        Returns:
            dict: A dictionary containing quote data (e.g., last price, volume, change).
                  Returns None if data cannot be fetched or on error.
        """
        endpoint = "market/quote/" + symbol + ".json"
        # E*Trade API often has a `detailFlag` parameter to control data verbosity.
        # Check E*Trade API docs for exact parameters for quotes.
        params = {"detailFlag": "ALL"} # 'ALL' or 'FUNDAMENTAL' or 'OPTIONS' etc.
        data = self._make_api_call(endpoint, params)

        if data and 'QuoteResponse' in data and 'QuoteData' in data['QuoteResponse']:
            # E*Trade API returns a list of QuoteData even for a single symbol
            if data['QuoteResponse']['QuoteData']:
                quote_data = data['QuoteResponse']['QuoteData'][0]
                # Extract relevant fields (adjust based on actual E*Trade response)
                return {
                    "symbol": quote_data.get('product', {}).get('symbol'),
                    "lastPrice": quote_data.get('All', {}).get('lastTrade'),
                    "changePct": quote_data.get('All', {}).get('changeClosePercentage'),
                    "volume": quote_data.get('All', {}).get('totalVolume'),
                    "bid": quote_data.get('All', {}).get('bid'),
                    "ask": quote_data.get('All', {}).get('ask'),
                    "high": quote_data.get('All', {}).get('high'),
                    "low": quote_data.get('All', {}).get('low'),
                    "open": quote_data.get('All', {}).get('open'),
                    "close": quote_data.get('All', {}).get('previousClose')
                }
        logger.warning(f"Failed to get quote for {symbol}.")
        return None

    def get_historical_data(self, symbol: str, interval: str = "1day", period: str = "3months") -> list:
        """
        Fetches historical data for a given stock symbol.

        Args:
            symbol (str): The stock ticker symbol.
            interval (str): Time interval (e.g., "1day", "5min"). Check E*Trade API docs.
            period (str): Historical period (e.g., "3months", "1year"). Check E*Trade API docs.

        Returns:
            list: A list of dictionaries, each representing a historical data point
                  (e.g., {'date': 'YYYY-MM-DD', 'open': X, 'high': Y, ...}).
                  Returns an empty list if data cannot be fetched.
        """
        # E*Trade API may have separate endpoints or parameters for historical data.
        # This is a conceptual endpoint. Refer to E*Trade docs for exact path and params.
        endpoint = f"market/history/{symbol}.json"
        params = {
            "interval": interval,
            "period": period,
            # Other parameters like startDate, endDate, marketSession etc.
        }
        data = self._make_api_call(endpoint, params)

        # Parse historical data response
        if data and 'IntradayCandleResponse' in data and 'Candle' in data['IntradayCandleResponse']:
             historical_candles = data['IntradayCandleResponse']['Candle']
             parsed_data = []
             for candle in historical_candles:
                 parsed_data.append({
                     'date': candle.get('dateTime'), # Or convert timestamp
                     'open': candle.get('open'),
                     'high': candle.get('high'),
                     'low': candle.get('low'),
                     'close': candle.get('close'),
                     'volume': candle.get('volume')
                 })
             return parsed_data
        elif data and 'HistoricalQuoteResponse' in data and 'QuoteData' in data['HistoricalQuoteResponse']:
            # For longer historical data, it might be in a different format
            historical_quotes = data['HistoricalQuoteResponse']['QuoteData']
            parsed_data = []
            for quote in historical_quotes:
                parsed_data.append({
                    'date': quote.get('dateTime'), # Or convert timestamp
                    'open': quote.get('open'),
                    'high': quote.get('high'),
                    'low': quote.get('low'),
                    'close': quote.get('close'),
                    'volume': quote.get('totalVolume')
                })
            return parsed_data
        logger.warning(f"No historical data received for {symbol}.")
        return []

    def get_news_sentiment(self, symbol: str) -> dict:
        """
        Fetches news and sentiment data for a given stock symbol.
        E*Trade's API might provide news, but explicit "sentiment" data (e.g., NLP-derived)
        might be limited or require third-party integration. This assumes E*Trade provides some.

        Args:
            symbol (str): The stock ticker symbol.

        Returns:
            dict: A dictionary containing news headlines and implied sentiment.
                  Returns an empty dictionary if data cannot be fetched.
        """
        # E*Trade API has a news endpoint: https://apisb.etrade.com/v1/market/news.json
        endpoint = "market/news.json"
        params = {"symbols": symbol} # Filter news by symbol
        data = self._make_api_call(endpoint, params)

        sentiment_info = {
            "earningsNews": "Not available from E*Trade API directly as 'earnings news' field.",
            "marketSentiment": "General market sentiment not directly provided by E*Trade news API.",
            "analystRatings": "Analyst ratings not directly provided by E*Trade news API."
        }
        if data and 'NewsResponse' in data and 'News' in data['NewsResponse']:
            news_items = data['NewsResponse']['News']
            headlines = [item.get('headline') for item in news_items if item.get('headline')]
            if headlines:
                sentiment_info['latest_headlines'] = headlines
                sentiment_info['earningsNews'] = f"Recent news headlines for {symbol}: {', '.join(headlines[:3])}..."
                # Basic sentiment inference could be done here based on keywords, but needs NLP
                # For now, just present the headlines.
        logger.warning(f"No specific sentiment data (beyond headlines) for {symbol} from E*Trade news API.")
        return sentiment_info