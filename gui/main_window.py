from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QTabWidget, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QTimer
from etrade_api.api_connection import ETradeAPIConnection
from etrade_api.market_data import MarketData
from etrade_api.trading import Trading
from ai.mistral_agent import MistralAgent
from simulation.simulator import Simulator
from user_data.user_config import UserConfig
from user_data.portfolio import Portfolio
from utils.logging import get_logger
import logging

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """
    The main window of the Mistral E*Trade GUI Stock Assistant.
    Manages all GUI components, user interactions, and orchestrates
    communication between different application modules (API, AI, Simulation).
    """
    def __init__(self):
        """
        Initializes the main window, sets up the UI, connects signals/slots,
        and initializes core application components.
        """
        super().__init__()
        self.setWindowTitle("Mistral E*Trade Stock Assistant")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize core components
        self.api_connection = ETradeAPIConnection()
        self.market_data = MarketData(self.api_connection)
        self.trading = Trading(self.api_connection)
        self.mistral_agent = MistralAgent()
        self.simulator = Simulator()
        self.user_config = UserConfig()
        self.portfolio = Portfolio()

        self.current_mode = "Test" # Default to Test Mode
        self.risk_level = self.user_config.get_risk_profile() # Load initial risk level

        self._setup_ui()
        self._setup_timers()
        self._load_initial_data()

    def _setup_ui(self):
        """
        Sets up the main layout and all individual UI components.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel: Controls and Settings ---
        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Mode Toggle
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Operating Mode:"))
        self.mode_toggle = QComboBox()
        self.mode_toggle.addItems(["Test", "Live"])
        self.mode_toggle.setCurrentText(self.current_mode)
        self.mode_toggle.currentIndexChanged.connect(self._toggle_mode)
        mode_layout.addWidget(self.mode_toggle)
        left_panel.addLayout(mode_layout)

        # Risk Profile Settings
        risk_layout = QHBoxLayout()
        risk_layout.addWidget(QLabel("Risk Profile:"))
        self.risk_dropdown = QComboBox()
        self.risk_dropdown.addItems(["Low", "Medium", "High"])
        self.risk_dropdown.setCurrentText(self.risk_level)
        self.risk_dropdown.currentIndexChanged.connect(self._update_risk_profile)
        risk_layout.addWidget(self.risk_dropdown)
        left_panel.addLayout(risk_layout)

        # Manual Retrain Button (Placeholder for future functionality)
        self.retrain_button = QPushButton("Manual Retrain Mistral (Coming Soon)")
        self.retrain_button.setEnabled(False) # Temporarily disabled
        left_panel.addWidget(self.retrain_button)
        left_panel.addStretch(1) # Pushes content to the top

        main_layout.addLayout(left_panel, 1) # Give left panel 1 part of space

        # --- Right Panel: Main Content Tabs ---
        right_panel = QVBoxLayout()
        self.tab_widget = QTabWidget()

        self._setup_ticker_panel()
        self._setup_recommendations_panel()
        self._setup_portfolio_panel()
        self._setup_logging_panel()

        self.tab_widget.addTab(self.ticker_panel_widget, "Real-time Ticker")
        self.tab_widget.addTab(self.recommendations_panel_widget, "Recommendations")
        self.tab_widget.addTab(self.portfolio_panel_widget, "Portfolio")
        self.tab_widget.addTab(self.logging_panel_widget, "Logs")

        right_panel.addWidget(self.tab_widget)
        main_layout.addLayout(right_panel, 4) # Give right panel 4 parts of space

        # Apply styles
        try:
            with open("gui/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            logger.warning("styles.qss not found. Running with default styles.")

    def _setup_ticker_panel(self):
        """Creates the real-time ticker tracking and alerts panel."""
        self.ticker_panel_widget = QWidget()
        layout = QVBoxLayout(self.ticker_panel_widget)
        layout.addWidget(QLabel("<h2>Real-time Ticker Tracking</h2>"))

        # Input for adding tickers
        ticker_input_layout = QHBoxLayout()
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("Enter Ticker Symbol (e.g., AAPL)")
        add_ticker_button = QPushButton("Add Ticker")
        add_ticker_button.clicked.connect(self._add_ticker)
        ticker_input_layout.addWidget(self.ticker_input)
        ticker_input_layout.addWidget(add_ticker_button)
        layout.addLayout(ticker_input_layout)

        # Table for displaying real-time data
        self.ticker_table = QTableWidget()
        self.ticker_table.setColumnCount(4)
        self.ticker_table.setHorizontalHeaderLabels(["Ticker", "Last Price", "Change (%)", "Volume"])
        self.ticker_table.horizontalHeader().setStretchLastSection(True)
        self.ticker_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.ticker_table)

        self.tracked_tickers = [] # List to store tickers being tracked

    def _setup_recommendations_panel(self):
        """Creates the structured recommended trades panel."""
        self.recommendations_panel_widget = QWidget()
        layout = QVBoxLayout(self.recommendations_panel_widget)
        layout.addWidget(QLabel("<h2>Investment Recommendations</h2>"))

        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(7)
        self.recommendations_table.setHorizontalHeaderLabels([
            "Ticker", "Confidence (%)", "Risk Level", "Suggested Action",
            "Time Horizon", "Reasoning", "Execute"
        ])
        self.recommendations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.recommendations_table)

    def _setup_portfolio_panel(self):
        """Creates the real-time portfolio management panel."""
        self.portfolio_panel_widget = QWidget()
        layout = QVBoxLayout(self.portfolio_panel_widget)
        layout.addWidget(QLabel("<h2>Portfolio Management</h2>"))

        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(5)
        self.portfolio_table.setHorizontalHeaderLabels(["Ticker", "Quantity", "Avg. Cost", "Current Price", "Unrealized P/L"])
        self.portfolio_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.portfolio_table)

        # Total portfolio value display
        self.total_portfolio_value_label = QLabel("Total Portfolio Value: $0.00")
        layout.addWidget(self.total_portfolio_value_label)


    def _setup_logging_panel(self):
        """Creates the clear logging area."""
        self.logging_panel_widget = QWidget()
        layout = QVBoxLayout(self.logging_panel_widget)
        layout.addWidget(QLabel("<h2>Application Logs</h2>"))

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        # Redirect standard logging to the QTextEdit
        self.log_handler = QtTextEditHandler(self.log_display)
        self.log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.log_handler)

    def _setup_timers(self):
        """
        Sets up QTimers for periodic data updates and AI analysis.
        """
        # Timer for real-time market data updates (e.g., every 5 seconds)
        self.market_data_timer = QTimer(self)
        self.market_data_timer.setInterval(5000) # 5 seconds
        self.market_data_timer.timeout.connect(self._update_market_data)
        self.market_data_timer.start()

        # Timer for AI analysis and recommendation generation (e.g., every 30 seconds)
        self.ai_analysis_timer = QTimer(self)
        self.ai_analysis_timer.setInterval(30000) # 30 seconds
        self.ai_analysis_timer.timeout.connect(self._run_ai_analysis)
        self.ai_analysis_timer.start()

        # Timer for portfolio updates (e.g., every 10 seconds)
        self.portfolio_update_timer = QTimer(self)
        self.portfolio_update_timer.setInterval(10000) # 10 seconds
        self.portfolio_update_timer.timeout.connect(self._update_portfolio_display)
        self.portfolio_update_timer.start()

    def _load_initial_data(self):
        """
        Loads initial configuration and portfolio data when the application starts.
        """
        self.portfolio.load_portfolio() # Load test mode portfolio
        self._update_portfolio_display()
        logger.info("Application initialized. Awaiting E*Trade API connection.")
        # Attempt to get OAuth access token at startup
        self._authenticate_etrade()


    def _authenticate_etrade(self):
        """
        Attempts to authenticate with E*Trade API using OAuth.
        This will typically open a browser for the user to authorize.
        """
        logger.info("Attempting E*Trade API authentication...")
        try:
            # This method in ETradeAPIConnection should handle the full OAuth flow
            # including opening a browser and waiting for user input (if needed for verifier).
            # For a GUI app, you might need a separate dialog for the verifier.
            # For simplicity here, assuming api_connection handles it internally.
            if self.api_connection.get_access_token():
                logger.info("E*Trade API authenticated successfully.")
            else:
                logger.warning("E*Trade API authentication failed or not completed.")
        except Exception as e:
            logger.error(f"Error during E*Trade API authentication: {e}")

    def _toggle_mode(self, index):
        """
        Toggles between Test (Simulation) and Live trading modes.
        """
        selected_mode = self.mode_toggle.itemText(index)
        if selected_mode == "Live":
            confirm = self.show_confirmation_dialog("Switch to Live Mode?",
                                                    "Are you sure you want to switch to LIVE trading mode? "
                                                    "Real money will be used for trades.")
            if not confirm:
                self.mode_toggle.setCurrentText(self.current_mode) # Revert selection
                return
            else:
                logger.warning("Switched to LIVE trading mode. All confirmed trades will be real.")
        else:
            logger.info("Switched to TEST (Simulation) mode. No real money will be used.")

        self.current_mode = selected_mode
        # Update any UI elements that depend on the mode, e.g., enabling/disabling trade buttons
        self._update_ui_for_mode()

    def _update_ui_for_mode(self):
        """Adjusts GUI elements based on the current operating mode."""
        # For now, mainly affects logging and confirmation messages.
        # Future: potentially grey out or change color of certain buttons in test mode.
        pass

    def _update_risk_profile(self, index):
        """
        Updates the user's risk profile based on dropdown selection.
        """
        self.risk_level = self.risk_dropdown.itemText(index)
        self.user_config.save_risk_profile(self.risk_level)
        logger.info(f"Risk profile updated to: {self.risk_level}")
        # Trigger re-evaluation of recommendations if needed
        self._run_ai_analysis()

    def _add_ticker(self):
        """
        Adds a ticker symbol to the tracked list and updates the display.
        """
        ticker = self.ticker_input.text().strip().upper()
        if ticker and ticker not in self.tracked_tickers:
            self.tracked_tickers.append(ticker)
            self.ticker_input.clear()
            logger.info(f"Added '{ticker}' to tracked tickers.")
            self._update_market_data() # Immediately fetch data for new ticker
        elif ticker:
            logger.warning(f"'{ticker}' is already being tracked.")
        else:
            logger.warning("Ticker input cannot be empty.")

    def _update_market_data(self):
        """
        Fetches real-time market data for tracked tickers from E*Trade API
        and updates the ticker display table.
        """
        if not self.api_connection.is_authenticated():
            logger.warning("E*Trade API not authenticated. Cannot fetch market data.")
            return

        # Clear existing rows to refresh
        self.ticker_table.setRowCount(0)

        for ticker in self.tracked_tickers:
            try:
                # E*Trade API call for real-time data
                data = self.market_data.get_quote(ticker)
                if data:
                    row_position = self.ticker_table.rowCount()
                    self.ticker_table.insertRow(row_position)

                    last_price = data.get('lastPrice', 'N/A')
                    change_percent = data.get('changePct', 'N/A')
                    volume = data.get('volume', 'N/A')

                    self.ticker_table.setItem(row_position, 0, QTableWidgetItem(ticker))
                    self.ticker_table.setItem(row_position, 1, QTableWidgetItem(str(last_price)))
                    self.ticker_table.setItem(row_position, 2, QTableWidgetItem(f"{change_percent}%"))
                    self.ticker_table.setItem(row_position, 3, QTableWidgetItem(str(volume)))
                else:
                    logger.warning(f"No market data received for {ticker} from E*Trade API.")
            except Exception as e:
                logger.error(f"Error fetching market data for {ticker}: {e}")
                self.ticker_table.insertRow(self.ticker_table.rowCount())
                self.ticker_table.setItem(self.ticker_table.rowCount() - 1, 0, QTableWidgetItem(ticker))
                self.ticker_table.setItem(self.ticker_table.rowCount() - 1, 1, QTableWidgetItem("Error"))
                self.ticker_table.setItem(self.ticker_table.rowCount() - 1, 2, QTableWidgetItem("Error"))
                self.ticker_table.setItem(self.ticker_table.rowCount() - 1, 3, QTableWidgetItem("Error"))


    def _run_ai_analysis(self):
        """
        Triggers the Mistral AI agent to analyze market data and generate recommendations.
        """
        if not self.api_connection.is_authenticated():
            logger.warning("E*Trade API not authenticated. Skipping AI analysis.")
            return

        logger.info("Running AI analysis for stock recommendations...")
        self.recommendations_table.setRowCount(0) # Clear previous recommendations

        # For demonstration, let's assume we fetch some data for analysis
        # In a real scenario, this would involve more comprehensive data fetching (charts, indicators etc.)
        for ticker in self.tracked_tickers:
            historical_data = self.market_data.get_historical_data(ticker, "1month", "daily") # Example
            sentiment_data = self.market_data.get_news_sentiment(ticker) # Example

            # Combine data and feed to Mistral
            # The prompt engineering is crucial here as defined in ai/prompts.py
            analysis_input = {
                "ticker": ticker,
                "real_time_quote": self.market_data.get_quote(ticker),
                "historical_data": historical_data,
                "sentiment_data": sentiment_data,
                "user_risk_profile": self.risk_level
            }

            try:
                recommendation = self.mistral_agent.generate_recommendation(analysis_input)
                self._display_recommendation(recommendation)
            except Exception as e:
                logger.error(f"Error generating recommendation for {ticker}: {e}")
                # Log the error in the recommendations panel or a dedicated error area.
                error_row = self.recommendations_table.rowCount()
                self.recommendations_table.insertRow(error_row)
                self.recommendations_table.setItem(error_row, 0, QTableWidgetItem(ticker))
                self.recommendations_table.setItem(error_row, 1, QTableWidgetItem("N/A"))
                self.recommendations_table.setItem(error_row, 2, QTableWidgetItem("N/A"))
                self.recommendations_table.setItem(error_row, 3, QTableWidgetItem("ERROR"))
                self.recommendations_table.setItem(error_row, 4, QTableWidgetItem("N/A"))
                self.recommendations_table.setItem(error_row, 5, QTableWidgetItem(f"AI Error: {e}"))
                self.recommendations_table.setItem(error_row, 6, QTableWidgetItem("N/A")) # No execute button

    def _display_recommendation(self, recommendation):
        """
        Displays a structured investment recommendation in the recommendations table.
        Filters based on user risk profile.
        """
        if not recommendation:
            return

        # Apply risk management filter
        if not self._check_risk_tolerance(recommendation):
            logger.info(f"Recommendation for {recommendation['Ticker']} omitted due to risk tolerance.")
            return

        row_position = self.recommendations_table.rowCount()
        self.recommendations_table.insertRow(row_position)

        self.recommendations_table.setItem(row_position, 0, QTableWidgetItem(recommendation.get('Ticker', 'N/A')))
        self.recommendations_table.setItem(row_position, 1, QTableWidgetItem(f"{recommendation.get('Confidence', 'N/A')}%"))
        self.recommendations_table.setItem(row_position, 2, QTableWidgetItem(recommendation.get('Risk Level', 'N/A')))
        self.recommendations_table.setItem(row_position, 3, QTableWidgetItem(recommendation.get('Suggested Action', 'N/A')))
        self.recommendations_table.setItem(row_position, 4, QTableWidgetItem(recommendation.get('Expected Time Horizon', 'N/A')))
        self.recommendations_table.setItem(row_position, 5, QTableWidgetItem(recommendation.get('Reasoning Summary', 'N/A')))

        # Add an "Execute" button for user confirmation
        execute_button = QPushButton("Execute")
        execute_button.clicked.connect(lambda: self._execute_trade(recommendation))
        self.recommendations_table.setCellWidget(row_position, 6, execute_button)
        logger.info(f"Displayed recommendation for {recommendation.get('Ticker')}")

    def _check_risk_tolerance(self, recommendation):
        """
        Checks if a recommendation aligns with the user's defined risk tolerance.
        This is a simplified example.
        """
        rec_risk = recommendation.get('Risk Level', 'Medium').lower()
        user_risk = self.risk_level.lower()

        risk_map = {"low": 1, "medium": 2, "high": 3}

        if risk_map.get(rec_risk, 2) > risk_map.get(user_risk, 2):
            return False # Recommendation risk is higher than user's tolerance
        return True


    def _execute_trade(self, recommendation):
        """
        Initiates a trade execution based on the recommendation,
        respecting the current mode (Test/Live) and requiring user confirmation for Live.
        """
        ticker = recommendation.get('Ticker')
        action = recommendation.get('Suggested Action')
        # Placeholder for quantity and order type determination (would be more complex)
        quantity = 10
        order_type = "MARKET"

        logger.info(f"Attempting to execute {action} order for {quantity} shares of {ticker}...")

        if self.current_mode == "Test":
            log_prefix = "SIMULATION – NO REAL MONEY USED."
            logger.info(f"{log_prefix} Executing simulated {action} for {ticker}.")
            self.simulator.execute_simulated_trade(ticker, action, quantity, self.portfolio)
            self._update_portfolio_display()
            self.show_information_dialog("Simulation Complete",
                                         f"{log_prefix} Simulated {action} of {quantity} {ticker} executed.")
        elif self.current_mode == "Live":
            confirm = self.show_confirmation_dialog("Confirm Live Trade",
                                                    f"Are you sure you want to execute a LIVE {action} order for {quantity} shares of {ticker}?")
            if confirm:
                logger.info(f"User confirmed LIVE {action} for {ticker}. Calling E*Trade API.")
                try:
                    # E*Trade API call for trade execution
                    trade_response = self.trading.place_order(
                        account_id=self.api_connection.account_id, # Assumes account_id is available after auth
                        symbol=ticker,
                        action=action,
                        quantity=quantity,
                        order_type=order_type
                    )
                    if trade_response and trade_response.get('orderId'):
                        logger.info(f"LIVE Trade executed successfully for {ticker}. Order ID: {trade_response['orderId']}")
                        self.show_information_dialog("Live Trade Successful",
                                                     f"LIVE {action} of {quantity} {ticker} placed. Order ID: {trade_response['orderId']}")
                        # Update portfolio (might need to fetch live portfolio after successful trade)
                        self._update_portfolio_display()
                    else:
                        logger.error(f"LIVE Trade failed for {ticker}. Response: {trade_response}")
                        self.show_error_dialog("Live Trade Failed",
                                               f"Failed to place {action} order for {ticker}. Check logs for details.")
                except Exception as e:
                    logger.error(f"Error during LIVE trade execution for {ticker}: {e}")
                    self.show_error_dialog("Live Trade Error",
                                           f"An error occurred during live trade for {ticker}: {e}")
            else:
                logger.info(f"User cancelled LIVE {action} for {ticker}.")
        self._update_portfolio_display() # Refresh portfolio display after potential trade

    def _update_portfolio_display(self):
        """
        Updates the portfolio management panel with current holdings.
        For live mode, this would involve fetching current portfolio from E*Trade.
        For test mode, it uses the local simulator portfolio.
        """
        self.portfolio_table.setRowCount(0)
        current_holdings = {}

        if self.current_mode == "Test":
            current_holdings = self.portfolio.get_holdings()
            logger.debug("Updating portfolio display from simulated holdings.")
        elif self.current_mode == "Live":
            if self.api_connection.is_authenticated() and self.api_connection.account_id:
                try:
                    # E*Trade API call for live portfolio holdings
                    live_portfolio = self.trading.get_portfolio(self.api_connection.account_id)
                    current_holdings = {item['symbol']: {'quantity': item['quantity'], 'costBasis': item.get('costBasis', 0)}
                                        for item in live_portfolio}
                    logger.debug("Updating portfolio display from LIVE E*Trade holdings.")
                except Exception as e:
                    logger.error(f"Error fetching live portfolio from E*Trade: {e}")
                    self.show_error_dialog("Portfolio Error", "Could not fetch live portfolio from E*Trade.")
            else:
                logger.warning("E*Trade API not authenticated or account ID not available for live portfolio.")


        total_value = 0
        for ticker, data in current_holdings.items():
            row_position = self.portfolio_table.rowCount()
            self.portfolio_table.insertRow(row_position)

            quantity = data.get('quantity', 0)
            avg_cost = data.get('costBasis', 0)
            current_price = "N/A"
            unrealized_pl = "N/A"

            # Try to get current price for P/L calculation
            quote_data = self.market_data.get_quote(ticker)
            if quote_data and quote_data.get('lastPrice'):
                current_price = quote_data['lastPrice']
                if quantity > 0 and isinstance(current_price, (int, float)) and isinstance(avg_cost, (int, float)):
                    unrealized_pl = (current_price - avg_cost) * quantity
                    total_value += current_price * quantity
            else:
                logger.warning(f"Could not get current price for {ticker} to update portfolio P/L.")

            self.portfolio_table.setItem(row_position, 0, QTableWidgetItem(ticker))
            self.portfolio_table.setItem(row_position, 1, QTableWidgetItem(str(quantity)))
            self.portfolio_table.setItem(row_position, 2, QTableWidgetItem(f"${avg_cost:.2f}"))
            self.portfolio_table.setItem(row_position, 3, QTableWidgetItem(f"${current_price:.2f}" if isinstance(current_price, (int, float)) else str(current_price)))
            self.portfolio_table.setItem(row_position, 4, QTableWidgetItem(f"${unrealized_pl:.2f}" if isinstance(unrealized_pl, (int, float)) else str(unrealized_pl)))

        self.total_portfolio_value_label.setText(f"Total Portfolio Value: ${total_value:.2f}")


    def show_confirmation_dialog(self, title, message):
        """Displays a confirmation dialog and returns True if confirmed, False otherwise."""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, title, message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def show_information_dialog(self, title, message):
        """Displays an information dialog."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)

    def show_error_dialog(self, title, message):
        """Displays an error dialog."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)


class QtTextEditHandler(logging.Handler):
    """
    A custom logging handler that redirects log records to a QTextEdit widget.
    """
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        # Append message to QTextEdit in the main GUI thread
        # Use a lambda to avoid direct UI manipulation from a non-GUI thread if logging is async
        self.text_edit.append(msg)