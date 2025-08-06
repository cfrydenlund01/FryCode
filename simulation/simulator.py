from user_data.portfolio import Portfolio
from utils.logging import get_logger

logger = get_logger(__name__)

class Simulator:
    """
    Manages simulated trade execution and updates a local portfolio.
    This module operates independently of the E*Trade API.
    """
    def __init__(self):
        """
        Initializes the simulator.
        """
        pass # The portfolio object is passed to execution methods

    def execute_simulated_trade(self, ticker: str, action: str, quantity: int, portfolio: Portfolio):
        """
        Executes a simulated buy or sell trade and updates the local portfolio.

        Args:
            ticker (str): The stock ticker symbol.
            action (str): "BUY" or "SELL".
            quantity (int): The number of shares.
            portfolio (Portfolio): The Portfolio object to update.
        """
        current_holdings = portfolio.get_holdings()

        if action.upper() == "BUY":
            # For simulation, assume price is last known price or a nominal value
            # In a real simulation, you'd want to fetch a simulated 'executed' price
            simulated_price = 100.00 # Placeholder: could fetch last known real price if available
            current_shares = current_holdings.get(ticker, {'quantity': 0, 'costBasis': 0})
            
            old_quantity = current_shares['quantity']
            old_cost_basis_total = old_quantity * current_shares['costBasis']

            new_quantity = old_quantity + quantity
            new_cost_basis_total = old_cost_basis_total + (quantity * simulated_price)
            new_avg_cost = new_cost_basis_total / new_quantity if new_quantity > 0 else 0

            portfolio.add_holding(ticker, new_quantity, new_avg_cost)
            logger.info(f"SIMULATION – NO REAL MONEY USED. Simulated BUY {quantity} shares of {ticker} at ${simulated_price:.2f}.")

        elif action.upper() == "SELL":
            current_shares = current_holdings.get(ticker, {'quantity': 0, 'costBasis': 0})
            if current_shares['quantity'] >= quantity:
                # For simulation, assume price is last known price or a nominal value
                simulated_price = 100.00 # Placeholder
                
                old_quantity = current_shares['quantity']
                old_cost_basis_total = old_quantity * current_shares['costBasis']

                new_quantity = old_quantity - quantity
                
                # Simplified cost basis adjustment for selling:
                # If selling all, cost basis becomes 0. If selling partial, recalculate.
                if new_quantity == 0:
                    new_avg_cost = 0
                else:
                    # Proportionally remove cost basis of sold shares. This is a simplification.
                    # FIFO/LIFO/Avg Cost for real accounting is complex.
                    new_cost_basis_total = old_cost_basis_total * (new_quantity / old_quantity) if old_quantity > 0 else 0
                    new_avg_cost = new_cost_basis_total / new_quantity

                portfolio.add_holding(ticker, new_quantity, new_avg_cost) # Use add_holding to update
                logger.info(f"SIMULATION – NO REAL MONEY USED. Simulated SELL {quantity} shares of {ticker} at ${simulated_price:.2f}.")
            else:
                logger.warning(f"SIMULATION – Cannot SELL {quantity} shares of {ticker}. Only {current_shares['quantity']} available.")
        else:
            logger.warning(f"SIMULATION – Invalid trade action: {action}.")