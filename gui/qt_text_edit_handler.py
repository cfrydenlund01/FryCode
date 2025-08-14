import logging
from PyQt6.QtWidgets import QTextEdit


class QtTextEditHandler(logging.Handler):
    """
    A custom logging handler that redirects log records to a QTextEdit widget.
    """

    def __init__(self, text_edit: QTextEdit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)
