from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt

class LogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        log_group = QGroupBox("Send/Receive")
        log_layout = QVBoxLayout()

        send_layout = QHBoxLayout()
        self.send_textbox = QLineEdit()
        self.send_button = QPushButton("Send")
        send_layout.addWidget(self.send_textbox)
        send_layout.addWidget(self.send_button)

        self.receive_textbox = QTextEdit()
        self.receive_textbox.setReadOnly(True)
        self.clear_button = QPushButton("Clear")

        log_layout.addLayout(send_layout)
        log_layout.addWidget(self.receive_textbox)
        log_layout.addWidget(self.clear_button, alignment=Qt.AlignRight)

        log_group.setLayout(log_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(log_group)
        self.setLayout(main_layout)
