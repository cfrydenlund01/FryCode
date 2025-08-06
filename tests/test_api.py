import unittest
import os
from etrade_api.api_connection import ETradeAPIConnection
from etrade_api.market_data import MarketData
from etrade_api.trading import Trading
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

class TestETradeAPI(unittest.TestCase):
    """
    Unit and integration tests for E*Trade API connection, market data, and trading.
    NOTE: These tests require valid E*Trade API credentials (consumer key/secret)
    and should ideally be run against a sandbox environment.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up for all tests in this class. Authenticate once.
        """
        cls.consumer_key = os.getenv("ETRADE_CONSUMER_KEY")
        cls.consumer_secret = os.getenv("ETRADE_CONSUMER_SECRET")
        cls.account_id = os.getenv("ETRADE_ACCOUNT_ID") # For trading tests

        if not cls.consumer_key or not cls.consumer_secret:
            raise unittest.SkipTest("E*TRADE_CONSUMER_KEY or E*TRADE_CONSUMER_SECRET not set in .env. Skipping API tests.")

        cls.api_connection = ETradeAPIConnection()
        if not cls.api_connection.get_access_token():
            raise unittest.SkipTest("Failed to authenticate with E*Trade API. Skipping API tests.")
        
        # Ensure account ID is available if trading tests are to be run
        if not cls.account_id and cls.api_connection.account_id:
            cls.account_id = cls.api_connection.account_id
        
        cls.market_data = MarketData(cls.api_connection)
        cls.trading = Trading(cls.api_connection)

    def test_01_api_authentication(self):
        """Test if the API connection is authenticated."""
        self.assertTrue(self.api_connection.is_authenticated(), "API should be authenticated.")

    def test_02_get_quote(self):
        """Test fetching a real-time quote for a known symbol."""
        symbol = "AAPL" # Use a common, active stock
        quote = self.market_data.get_quote(symbol)
        self.assertIsNotNone(quote, f"Should receive a quote for {symbol}")
        self.assertIn('lastPrice', quote, "Quote should contain 'lastPrice'")
        self.assertIn('volume', quote, "Quote should contain 'volume'")
        self.assertEqual(quote.get('symbol'), symbol, f"Quote symbol should match {symbol}")

    def test_03_get_historical_data(self):
        """Test fetching historical data for a symbol."""
        symbol = "GOOG" # Another common symbol
        # E*Trade has specific intervals/periods. Using common ones for example.
        historical_data = self.market_data.get_historical_data(symbol, interval="1day", period="1month")
        self.assertIsNotNone(historical_data, f"Should receive historical data for {symbol}")
        self.assertIsInstance(historical_data, list, "Historical data should be a list")
        self.assertGreater(len(historical_data), 0, "Historical data list should not be empty")
        # Check structure of a single data point
        if historical_data:
            self.assertIn('close', historical_data[0], "Historical data point should contain 'close'")

    def test_04_get_news_sentiment(self):
        """Test fetching news/sentiment for a symbol."""
        symbol = "MSFT"
        sentiment = self.market_data.get_news_sentiment(symbol)
        self.assertIsNotNone(sentiment, f"Should receive sentiment data for {symbol}")
        self.assertIsInstance(sentiment, dict, "Sentiment data should be a dictionary")
        self.assertIn('latest_headlines', sentiment, "Sentiment should contain 'latest_headlines'")


    # Trading tests should only be run in Sandbox environment and with caution.
    # Requires a valid account_id.
    @unittest.skipUnless(os.getenv("ETRADE_SANDBOX_MODE") == "True" and os.getenv("ETRADE_ACCOUNT_ID"),
                         "Trading tests require ETRADE_SANDBOX_MODE=True and ETRADE_ACCOUNT_ID set.")
    def test_05_place_simulated_buy_order(self):
        """Test placing a simulated BUY order (requires sandbox and account_id)."""
        symbol = "TSLA"
        quantity = 1
        action = "BUY"
        order_type = "MARKET"

        # Note: E*Trade requires a 'preview' call before a 'place' call.
        # The trading.py module is designed to handle this, but the actual
        # `_make_api_post_call` for `place` needs the `previewId` or similar.
        # This test is conceptual and would need to mirror the exact preview-place flow.
        try:
            order_response = self.trading.place_order(
                account_id=self.account_id,
                symbol=symbol,
                action=action,
                quantity=quantity,
                order_type=order_type
            )
            self.assertIsNotNone(order_response, "Order response should not be None")
            self.assertIn('orderId', order_response.get('PlaceOrderResponse', {}), "Order response should contain orderId")
            self.assertTrue(order_response.get('PlaceOrderResponse', {}).get('orderId') is not None, "Order ID should be present")
        except Exception as e:
            self.fail(f"Failed to place simulated buy order: {e}")

    @unittest.skipUnless(os.getenv("ETRADE_SANDBOX_MODE") == "True" and os.getenv("ETRADE_ACCOUNT_ID"),
                         "Trading tests require ETRADE_SANDBOX_MODE=True and ETRADE_ACCOUNT_ID set.")
    def test_06_get_portfolio(self):
        """Test fetching portfolio holdings (requires sandbox and account_id)."""
        portfolio = self.trading.get_portfolio(self.account_id)
        self.assertIsNotNone(portfolio, "Portfolio should not be None")
        self.assertIsInstance(portfolio, list, "Portfolio should be a list")
        # Further checks can be done if you know expected holdings in sandbox.


if __name__ == '__main__':
    unittest.main()