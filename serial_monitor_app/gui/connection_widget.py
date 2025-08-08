
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QComboBox, QPushButton, QGroupBox
)

class ConnectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        connection_group = QGroupBox("Connection")
        connection_layout = QGridLayout()

        self.com_port_combo = QComboBox()
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_rate_combo.setCurrentText("9600")
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Odd", "Even"])
        self.open_button = QPushButton("Connect")
        self.close_button = QPushButton("Disconnect")
        self.close_button.setEnabled(False)

        connection_layout.addWidget(QLabel("COM Port:"), 0, 0)
        connection_layout.addWidget(self.com_port_combo, 0, 1)
        connection_layout.addWidget(QLabel("Baud Rate:"), 0, 2)
        connection_layout.addWidget(self.baud_rate_combo, 0, 3)
        connection_layout.addWidget(QLabel("Parity:"), 0, 4)
        connection_layout.addWidget(self.parity_combo, 0, 5)
        connection_layout.addWidget(self.open_button, 1, 0, 1, 3)
        connection_layout.addWidget(self.close_button, 1, 3, 1, 3)
        
        connection_group.setLayout(connection_layout)

        main_layout = QGridLayout(self)
        main_layout.addWidget(connection_group)
        self.setLayout(main_layout)
