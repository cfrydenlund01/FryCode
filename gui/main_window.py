from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTabWidget,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QTimer
from etrade_api.api_connection import ETradeAPIConnection
from etrade_api.market_data import MarketData
from etrade_api.trading import Trading
from etrade_api.exceptions import ETradeCredentialsMissing
from utils import credentials as cred
from ai.mistral_agent import MistralAgent
from simulation.simulator import Simulator
from user_data.user_config import UserConfig
from user_data.portfolio import Portfolio
from utils.logging import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    The main window of the Mistral E*Trade GUI Stock Assistant.
    Manages all GUI components, user interactions, and orchestrates
    communication between different application modules (API, AI, Simulation).
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mistral E*Trade Stock Assistant")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize core components without requiring credentials at startup
        self.api_connection = None
        self.market_data = None
        self.trading = None
        self.mistral_agent = MistralAgent()
        self.simulator = Simulator()
        self.user_config = UserConfig()
        self.portfolio = Portfolio()

        self.current_mode = "Test"
        self.risk_level = self.user_config.get_risk_profile()

        self._setup_ui()
        self._setup_timers()
        self._load_initial_data()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel: Controls and Settings ---
        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Credential Input Section
        left_panel.addWidget(QLabel("<h3>E*TRADE Credentials</h3>"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Consumer Key")
        self.secret_input = QLineEdit()
        self.secret_input.setPlaceholderText("Consumer Secret")
        self.secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.save_creds_button = QPushButton("Save Credentials")
        self.save_creds_button.clicked.connect(self._save_credentials)
        left_panel.addWidget(self.key_input)
        left_panel.addWidget(self.secret_input)
        left_panel.addWidget(self.save_creds_button)

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
        self.retrain_button.setEnabled(False)
        left_panel.addWidget(self.retrain_button)
        left_panel.addStretch(1)

        main_layout.addLayout(left_panel, 1)

        # --- Right Panel: Main Content Tabs ---
        right_panel = QVBoxLayout()
        self.tab_widget = QTabWidget()

        self._setup_ticker_panel()
        self._setup_recommendations_panel()
        self._setup_portfolio_panel()

        self.tab_widget.addTab(self.ticker_panel_widget, "Real-time Ticker")
        self.tab_widget.addTab(self.recommendations_panel_widget, "Recommendations")
        self.tab_widget.addTab(self.portfolio_panel_widget, "Portfolio")

        right_panel.addWidget(self.tab_widget)
        main_layout.addLayout(right_panel, 4)

        try:
            with open("gui/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            logger.warning("styles.qss not found. Running with default styles.")

    def _setup_ticker_panel(self):
        self.ticker_panel_widget = QWidget()
        layout = QVBoxLayout(self.ticker_panel_widget)
        layout.addWidget(QLabel("<h2>Real-time Ticker Tracking</h2>"))

        ticker_input_layout = QHBoxLayout()
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("Enter Ticker Symbol (e.g., AAPL)")
        add_ticker_button = QPushButton("Add Ticker")
        add_ticker_button.clicked.connect(self._add_ticker)
        ticker_input_layout.addWidget(self.ticker_input)
        ticker_input_layout.addWidget(add_ticker_button)
        layout.addLayout(ticker_input_layout)

        self.ticker_table = QTableWidget()
        self.ticker_table.setColumnCount(4)
        self.ticker_table.setHorizontalHeaderLabels(
            ["Ticker", "Last Price", "Change (%)", "Volume"]
        )
        self.ticker_table.horizontalHeader().setStretchLastSection(True)
        self.ticker_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.ticker_table)

        self.tracked_tickers = []

    def _setup_recommendations_panel(self):
        self.recommendations_panel_widget = QWidget()
        layout = QVBoxLayout(self.recommendations_panel_widget)
        layout.addWidget(QLabel("<h2>Investment Recommendations</h2>"))

        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(7)
        self.recommendations_table.setHorizontalHeaderLabels(
            [
                "Ticker",
                "Confidence (%)",
                "Risk Level",
                "Suggested Action",
                "Time Horizon",
                "Reasoning",
                "Execute",
            ]
        )
        self.recommendations_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.recommendations_table)

    def _setup_portfolio_panel(self):
        self.portfolio_panel_widget = QWidget()
        layout = QVBoxLayout(self.portfolio_panel_widget)
        layout.addWidget(QLabel("<h2>Portfolio Management</h2>"))

        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(5)
        self.portfolio_table.setHorizontalHeaderLabels(
            ["Ticker", "Quantity", "Avg. Cost", "Current Price", "Unrealized P/L"]
        )
        self.portfolio_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.portfolio_table)

        self.total_portfolio_value_label = QLabel("Total Portfolio Value: $0.00")
        layout.addWidget(self.total_portfolio_value_label)

    def _save_credentials(self):
        key = self.key_input.text().strip()
        secret = self.secret_input.text().strip()

        if not key or not secret:
            QMessageBox.warning(
                self,
                "Missing Credentials",
                "Please enter both a Consumer Key and a Consumer Secret.",
            )
            return

        cred.set_consumer_credentials(key, secret)
        QMessageBox.information(
            self,
            "Credentials Saved",
            "E*TRADE credentials have been saved to the secure store.",
        )
        logger.info("Credentials saved via GUI. Attempting to authenticate.")
        self._authenticate_etrade()

    def _setup_timers(self):
        self.market_data_timer = QTimer(self)
        self.market_data_timer.setInterval(5000)
        self.market_data_timer.timeout.connect(self._update_market_data)
        self.market_data_timer.start()

        self.ai_analysis_timer = QTimer(self)
        self.ai_analysis_timer.setInterval(30000)
        self.ai_analysis_timer.timeout.connect(self._run_ai_analysis)
        self.ai_analysis_timer.start()

        self.portfolio_update_timer = QTimer(self)
        self.portfolio_update_timer.setInterval(10000)
        self.portfolio_update_timer.timeout.connect(self._update_portfolio_display)
        self.portfolio_update_timer.start()

    def _load_initial_data(self):
        self.portfolio.load_portfolio()
        self._update_portfolio_display()
        logger.info("Application initialized. Awaiting E*Trade API connection.")
        self._authenticate_etrade()

    def _get_oauth_verifier_from_gui(self) -> str:
        """
        Pops up a dialog to ask the user for the OAuth verifier code.
        """
        dialog_title = "E*TRADE Authentication"
        dialog_text = "Please enter the verification code from the E*TRADE webpage:"
        verifier, ok = QInputDialog.getText(self, dialog_title, dialog_text)
        if ok and verifier:
            return verifier
        return ""

    def _authenticate_etrade(self):
        if self.api_connection:
            return

        logger.info("Attempting E*Trade API authentication...")
        try:
            self.api_connection = ETradeAPIConnection(
                get_verifier_callback=self._get_oauth_verifier_from_gui
            )
            if self.api_connection.get_access_token():
                logger.info("E*Trade API authenticated successfully.")
                self.market_data = MarketData(self.api_connection)
                self.trading = Trading(self.api_connection)
            else:
                logger.warning("E*Trade API authentication failed or not completed.")
        except ETradeCredentialsMissing:
            logger.warning(
                "E*Trade credentials missing. Please enter them in the left panel."
            )
        except Exception as e:
            logger.error(f"Error during E*Trade API authentication: {e}")

    def _toggle_mode(self, index):
        selected_mode = self.mode_toggle.itemText(index)
        if selected_mode == "Live":
            confirm = self._show_confirmation_dialog(
                "Switch to Live Mode?",
                "Are you sure you want to switch to LIVE trading mode? Real money will be used for trades.",
            )
            if not confirm:
                self.mode_toggle.setCurrentText(self.current_mode)
                return
            else:
                logger.warning(
                    "Switched to LIVE trading mode. All confirmed trades will be real."
                )
        else:
            logger.info(
                "Switched to TEST (Simulation) mode. No real money will be used."
            )

        self.current_mode = selected_mode
        self._update_ui_for_mode()

    def _update_ui_for_mode(self):
        pass

    def _update_risk_profile(self, index):
        self.risk_level = self.risk_dropdown.itemText(index)
        self.user_config.save_risk_profile(self.risk_level)
        logger.info(f"Risk profile updated to: {self.risk_level}")
        self._run_ai_analysis()

    def _add_ticker(self):
        ticker = self.ticker_input.text().strip().upper()
        if ticker and ticker not in self.tracked_tickers:
            self.tracked_tickers.append(ticker)
            self.ticker_input.clear()
            logger.info(f"Added '{ticker}' to tracked tickers.")
            self._update_market_data()
        elif ticker:
            logger.warning(f"'{ticker}' is already being tracked.")
        else:
            logger.warning("Ticker input cannot be empty.")

    def _update_market_data(self):
        if not self.api_connection or not self.api_connection.is_authenticated():
            logger.warning("E*Trade API not authenticated. Cannot fetch market data.")
            return

        self.ticker_table.setRowCount(0)

        for ticker in self.tracked_tickers:
            try:
                data = self.market_data.get_quote(ticker)
                if data:
                    row_position = self.ticker_table.rowCount()
                    self.ticker_table.insertRow(row_position)
                    last_price = data.get("lastPrice", "N/A")
                    change_percent = data.get("changePct", "N/A")
                    volume = data.get("volume", "N/A")
                    self.ticker_table.setItem(row_position, 0, QTableWidgetItem(ticker))
                    self.ticker_table.setItem(
                        row_position, 1, QTableWidgetItem(str(last_price))
                    )
                    self.ticker_table.setItem(
                        row_position, 2, QTableWidgetItem(f"{change_percent}%")
                    )
                    self.ticker_table.setItem(
                        row_position, 3, QTableWidgetItem(str(volume))
                    )
                else:
                    logger.warning(
                        f"No market data received for {ticker} from E*Trade API."
                    )
            except Exception as e:
                logger.error(f"Error fetching market data for {ticker}: {e}")
                self.ticker_table.insertRow(self.ticker_table.rowCount())
                self.ticker_table.setItem(
                    self.ticker_table.rowCount() - 1, 0, QTableWidgetItem(ticker)
                )
                self.ticker_table.setItem(
                    self.ticker_table.rowCount() - 1, 1, QTableWidgetItem("Error")
                )
                self.ticker_table.setItem(
                    self.ticker_table.rowCount() - 1, 2, QTableWidgetItem("Error")
                )
                self.ticker_table.setItem(
                    self.ticker_table.rowCount() - 1, 3, QTableWidgetItem("Error")
                )

    def _run_ai_analysis(self):
        if not self.api_connection or not self.api_connection.is_authenticated():
            logger.warning("E*Trade API not authenticated. Skipping AI analysis.")
            return

        logger.info("Running AI analysis for stock recommendations...")
        self.recommendations_table.setRowCount(0)

        for ticker in self.tracked_tickers:
            historical_data = self.market_data.get_historical_data(
                ticker, "1month", "daily"
            )
            sentiment_data = self.market_data.get_news_sentiment(ticker)
            analysis_input = {
                "ticker": ticker,
                "real_time_quote": self.market_data.get_quote(ticker),
                "historical_data": historical_data,
                "sentiment_data": sentiment_data,
                "user_risk_profile": self.risk_level,
            }
            try:
                recommendation = self.mistral_agent.generate_recommendation(
                    analysis_input
                )
                self._display_recommendation(recommendation)
            except Exception as e:
                logger.error(f"Error generating recommendation for {ticker}: {e}")
                error_row = self.recommendations_table.rowCount()
                self.recommendations_table.insertRow(error_row)
                self.recommendations_table.setItem(
                    error_row, 0, QTableWidgetItem(ticker)
                )
                self.recommendations_table.setItem(
                    error_row, 1, QTableWidgetItem("N/A")
                )
                self.recommendations_table.setItem(
                    error_row, 2, QTableWidgetItem("N/A")
                )
                self.recommendations_table.setItem(
                    error_row, 3, QTableWidgetItem("ERROR")
                )
                self.recommendations_table.setItem(
                    error_row, 4, QTableWidgetItem("N/A")
                )
                self.recommendations_table.setItem(
                    error_row, 5, QTableWidgetItem(f"AI Error: {e}")
                )
                self.recommendations_table.setItem(
                    error_row, 6, QTableWidgetItem("N/A")
                )

    def _display_recommendation(self, recommendation):
        if not recommendation:
            return

        if not self._check_risk_tolerance(recommendation):
            logger.info(
                f"Recommendation for {recommendation['Ticker']} omitted due to risk tolerance."
            )
            return

        row_position = self.recommendations_table.rowCount()
        self.recommendations_table.insertRow(row_position)
        self.recommendations_table.setItem(
            row_position, 0, QTableWidgetItem(recommendation.get("Ticker", "N/A"))
        )
        self.recommendations_table.setItem(
            row_position,
            1,
            QTableWidgetItem(f"{recommendation.get('Confidence', 'N/A')}%"),
        )
        self.recommendations_table.setItem(
            row_position, 2, QTableWidgetItem(recommendation.get("Risk Level", "N/A"))
        )
        self.recommendations_table.setItem(
            row_position,
            3,
            QTableWidgetItem(recommendation.get("Suggested Action", "N/A")),
        )
        self.recommendations_table.setItem(
            row_position,
            4,
            QTableWidgetItem(recommendation.get("Expected Time Horizon", "N/A")),
        )
        self.recommendations_table.setItem(
            row_position,
            5,
            QTableWidgetItem(recommendation.get("Reasoning Summary", "N/A")),
        )

        execute_button = QPushButton("Execute")
        execute_button.clicked.connect(lambda: self._execute_trade(recommendation))
        self.recommendations_table.setCellWidget(row_position, 6, execute_button)
        logger.info(f"Displayed recommendation for {recommendation.get('Ticker')}")

    def _check_risk_tolerance(self, recommendation):
        rec_risk = recommendation.get("Risk Level", "Medium").lower()
        user_risk = self.risk_level.lower()
        risk_map = {"low": 1, "medium": 2, "high": 3}
        if risk_map.get(rec_risk, 2) > risk_map.get(user_risk, 2):
            return False
        return True

    def _execute_trade(self, recommendation):
        ticker = recommendation.get("Ticker")
        action = recommendation.get("Suggested Action")
        quantity = 10
        order_type = "MARKET"

        logger.info(
            f"Attempting to execute {action} order for {quantity} shares of {ticker}..."
        )

        if self.current_mode == "Test":
            log_prefix = "SIMULATION – NO REAL MONEY USED."
            logger.info(f"{log_prefix} Executing simulated {action} for {ticker}.")
            self.simulator.execute_simulated_trade(
                ticker, action, quantity, self.portfolio
            )
            self._update_portfolio_display()
            self._show_information_dialog(
                "Simulation Complete",
                f"{log_prefix} Simulated {action} of {quantity} {ticker} executed.",
            )
        elif self.current_mode == "Live":
            confirm = self._show_confirmation_dialog(
                "Confirm Live Trade",
                f"Are you sure you want to execute a LIVE {action} order for {quantity} shares of {ticker}?",
            )
            if confirm:
                logger.info(
                    f"User confirmed LIVE {action} for {ticker}. Calling E*Trade API."
                )
                try:
                    trade_response = self.trading.place_order(
                        account_id=self.api_connection.account_id,
                        symbol=ticker,
                        action=action,
                        quantity=quantity,
                        order_type=order_type,
                    )
                    if trade_response and trade_response.get("orderId"):
                        logger.info(
                            f"LIVE Trade executed successfully for {ticker}. Order ID: {trade_response['orderId']}"
                        )
                        self._show_information_dialog(
                            "Live Trade Successful",
                            f"LIVE {action} of {quantity} {ticker} placed. Order ID: {trade_response['orderId']}",
                        )
                        self._update_portfolio_display()
                    else:
                        logger.error(
                            f"LIVE Trade failed for {ticker}. Response: {trade_response}"
                        )
                        self._show_error_dialog(
                            "Live Trade Failed",
                            f"Failed to place {action} order for {ticker}. Check logs for details.",
                        )
                except Exception as e:
                    logger.error(f"Error during LIVE trade execution for {ticker}: {e}")
                    self._show_error_dialog(
                        "Live Trade Error",
                        f"An error occurred during live trade for {ticker}: {e}",
                    )
            else:
                logger.info(f"User cancelled LIVE {action} for {ticker}.")
        self._update_portfolio_display()

    def _update_portfolio_display(self):
        if not self.api_connection or not self.api_connection.is_authenticated():
            logger.warning(
                "E*Trade API not authenticated. Displaying simulated portfolio."
            )
            current_holdings = self.portfolio.get_holdings()
            self.total_portfolio_value_label.setText(
                "Total Portfolio Value (Simulated): $0.00"
            )
        else:
            current_holdings = {}
            if self.current_mode == "Test":
                current_holdings = self.portfolio.get_holdings()
                logger.debug("Updating portfolio display from simulated holdings.")
            elif self.current_mode == "Live":
                try:
                    live_portfolio = self.trading.get_portfolio(
                        self.api_connection.account_id
                    )
                    current_holdings = {
                        item["symbol"]: {
                            "quantity": item["quantity"],
                            "costBasis": item.get("costBasis", 0),
                        }
                        for item in live_portfolio
                    }
                    logger.debug(
                        "Updating portfolio display from LIVE E*Trade holdings."
                    )
                except Exception as e:
                    logger.error(f"Error fetching live portfolio from E*Trade: {e}")
                    self._show_error_dialog(
                        "Portfolio Error",
                        "Could not fetch live portfolio from E*Trade.",
                    )

            total_value = 0
            self.portfolio_table.setRowCount(0)
            for ticker, data in current_holdings.items():
                row_position = self.portfolio_table.rowCount()
                self.portfolio_table.insertRow(row_position)
                quantity = data.get("quantity", 0)
                avg_cost = data.get("costBasis", 0)
                current_price = "N/A"
                unrealized_pl = "N/A"
                quote_data = self.market_data.get_quote(ticker)
                if quote_data and quote_data.get("lastPrice"):
                    current_price = quote_data["lastPrice"]
                    if (
                        quantity > 0
                        and isinstance(current_price, (int, float))
                        and isinstance(avg_cost, (int, float))
                    ):
                        unrealized_pl = (current_price - avg_cost) * quantity
                        total_value += current_price * quantity
                else:
                    logger.warning(
                        f"Could not get current price for {ticker} to update portfolio P/L."
                    )
                self.portfolio_table.setItem(row_position, 0, QTableWidgetItem(ticker))
                self.portfolio_table.setItem(
                    row_position, 1, QTableWidgetItem(str(quantity))
                )
                self.portfolio_table.setItem(
                    row_position, 2, QTableWidgetItem(f"${avg_cost:.2f}")
                )
                self.portfolio_table.setItem(
                    row_position,
                    3,
                    QTableWidgetItem(
                        f"${current_price:.2f}"
                        if isinstance(current_price, (int, float))
                        else str(current_price)
                    ),
                )
                self.portfolio_table.setItem(
                    row_position,
                    4,
                    QTableWidgetItem(
                        f"${unrealized_pl:.2f}"
                        if isinstance(unrealized_pl, (int, float))
                        else str(unrealized_pl)
                    ),
                )
            self.total_portfolio_value_label.setText(
                f"Total Portfolio Value: ${total_value:.2f}"
            )

    def _show_confirmation_dialog(self, title, message):
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _show_information_dialog(self, title, message):
        QMessageBox.information(self, title, message)

    def _show_error_dialog(self, title, message):
        QMessageBox.critical(self, title, message)
