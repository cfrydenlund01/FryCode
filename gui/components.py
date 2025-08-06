from PyQt6.QtWidgets import QPushButton, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget, QComboBox

class LabeledInput(QWidget):
    """
    A reusable custom widget combining a QLabel and a QLineEdit.
    """
    def __init__(self, label_text, placeholder_text="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.label = QLabel(label_text)
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder_text)
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.setContentsMargins(0, 0, 0, 0) # Remove extra margins

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)

# More reusable components can be added here as the UI complexity grows.