### `main.py`

#This is the entry point for the GUI application. It initializes the QApplication and the main window.

#```python

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from utils.logging import setup_logging
import os
from dotenv import load_dotenv

def main():
    """
    Main entry point for the Mistral E*Trade GUI Stock Assistant application.
    Initializes logging, loads environment variables, and starts the GUI.
    """
    load_dotenv() # Load environment variables from .env file
    setup_logging() # Set up application-wide logging

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
