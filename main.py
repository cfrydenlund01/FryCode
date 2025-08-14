### `main.py`

#This is the entry point for the GUI application. It initializes the QApplication and the main window.

#```python

import sys
import argparse
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from utils.logging import setup_logging
from dotenv import load_dotenv

def main() -> None:
    """Main entry point for the GUI application."""

    parser = argparse.ArgumentParser(
        description="Mistral E*Trade GUI Stock Assistant"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    load_dotenv()  # Load environment variables from .env file
    setup_logging(verbose=args.verbose)  # Set up application-wide logging

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
