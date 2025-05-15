from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
                            QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget, QHBoxLayout,
                            QListWidget, QDialog, QFormLayout, QDialogButtonBox)

class AddFavoriteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Favorito")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit()
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["PostgreSQL", "SQL Server", "MySQL"])
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.db_name_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("senha (opcional)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addRow("Nome:", self.name_input)
        layout.addRow("Tipo:", self.db_type_combo)
        layout.addRow("Host:", self.host_input)
        layout.addRow("Porta:", self.port_input)
        layout.addRow("Banco:", self.db_name_input)
        layout.addRow("Usuário:", self.username_input)
        layout.addRow("Senha:", self.password_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)