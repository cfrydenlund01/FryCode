import json
import os
from utils.logging import get_logger

logger = get_logger(__name__)

class Portfolio:
    """
    Manages the local portfolio storage for the simulation (test) mode.
    Handles loading, saving, and updating portfolio holdings.
    """
    def __init__(self):
        self.portfolio_file = "user_data/portfolio.json"
        self._holdings = self._load_portfolio_from_file()

    def _load_portfolio_from_file(self) -> dict:
        """
        Loads portfolio holdings from the JSON file.
        Returns an empty dictionary if the file doesn't exist or is invalid.
        """
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    holdings = json.load(f)
                    logger.info("Portfolio loaded successfully from file.")
                    return holdings
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding portfolio.json: {e}. Starting with empty portfolio.")
                return {}
            except Exception as e:
                logger.error(f"Error loading portfolio.json: {e}. Starting with empty portfolio.")
                return {}
        logger.info("portfolio.json not found. Starting with an empty portfolio.")
        return {}

    def save_portfolio(self):
        """
        Saves the current portfolio holdings to the JSON file.
        """
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump(self._holdings, f, indent=4)
            logger.info("Portfolio saved successfully to file.")
        except Exception as e:
            logger.error(f"Error saving portfolio to file: {e}")

    def get_holdings(self) -> dict:
        """
        Returns the current portfolio holdings.
        """
        return self._holdings

    def add_holding(self, symbol: str, quantity: int, average_cost: float):
        """
        Adds or updates a holding in the portfolio.
        For sales, quantity can be 0 or negative to reduce/remove.
        """
        if quantity < 0:
            logger.error(f"Cannot add negative quantity for {symbol}. Use reduce_holding or handle sale logic.")
            return

        # Ensure costBasis is correctly managed on additions/updates.
        # This simplified logic assumes average cost for additions.
        if symbol in self._holdings:
            existing_quantity = self._holdings[symbol]['quantity']
            existing_total_cost = existing_quantity * self._holdings[symbol]['costBasis']

            new_total_cost = existing_total_cost + (quantity * average_cost)
            new_total_quantity = existing_quantity + quantity

            self._holdings[symbol]['quantity'] = new_total_quantity
            self._holdings[symbol]['costBasis'] = new_total_cost / new_total_quantity if new_total_quantity > 0 else 0
        else:
            self._holdings[symbol] = {
                'quantity': quantity,
                'costBasis': average_cost
            }
        self.save_portfolio()
        logger.info(f"Updated holding for {symbol}: Quantity={self._holdings[symbol]['quantity']}, Avg. Cost=${self._holdings[symbol]['costBasis']:.2f}")


    def remove_holding(self, symbol: str):
        """
        Removes a holding from the portfolio (e.g., after selling all shares).
        """
        if symbol in self._holdings:
            del self._holdings[symbol]
            self.save_portfolio()
            logger.info(f"Removed {symbol} from portfolio.")

    def update_holding(self, symbol: str, new_quantity: int, new_cost_basis: float = None):
        """
        Directly updates the quantity and optionally the cost basis of a holding.
        Use with caution for sales where average cost needs recalculation.
        """
        if new_quantity <= 0:
            self.remove_holding(symbol)
            return

        if symbol in self._holdings:
            self._holdings[symbol]['quantity'] = new_quantity
            if new_cost_basis is not None:
                self._holdings[symbol]['costBasis'] = new_cost_basis
            logger.info(f"Directly updated {symbol} holding to quantity {new_quantity}.")
            self.save_portfolio()
        else:
            logger.warning(f"Attempted to update non-existent holding: {symbol}.")