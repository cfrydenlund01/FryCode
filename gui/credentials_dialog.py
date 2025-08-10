"""Dialog to collect E*TRADE consumer credentials."""

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
)


class CredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("E*TRADE Credentials")

        self.key_edit = QLineEdit()
        self.secret_edit = QLineEdit()
        self.secret_edit.setEchoMode(QLineEdit.EchoMode.Password)

        layout = QFormLayout(self)
        layout.addRow("Consumer Key", self.key_edit)
        layout.addRow("Consumer Secret", self.secret_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_credentials(self) -> tuple[str, str]:
        return self.key_edit.text().strip(), self.secret_edit.text().strip()

