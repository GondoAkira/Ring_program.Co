from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit, 
    QGroupBox, QHBoxLayout
)
from PySide6.QtCore import Signal

class ControlWidget(QWidget):
    command_to_send = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        top_level_layout = QHBoxLayout(self)
        top_level_layout.setContentsMargins(0, 0, 0, 0)

        main_layout = QVBoxLayout()

        # --- View Group ---
        view_group = QGroupBox("Views")
        view_layout = QVBoxLayout() # Changed to QVBoxLayout

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.show_values_button = QPushButton("Show Values")
        self.new_mem_graph_button = QPushButton("Graph")
        self.new_bk_graph_button = QPushButton("Err wave")
        self.show_eeprom_button = QPushButton("EEPROM")
        buttons_layout.addWidget(self.show_values_button)
        buttons_layout.addWidget(self.new_mem_graph_button)
        buttons_layout.addWidget(self.new_bk_graph_button)
        buttons_layout.addWidget(self.show_eeprom_button)
        buttons_layout.addStretch(1)
        view_layout.addLayout(buttons_layout)
        view_group.setLayout(view_layout)

        # --- Automation Group ---
        automation_group = QGroupBox("Automation")
        automation_layout = QGridLayout()
        self.auto_run_button = QPushButton("Auto Run")
        self.auto_run_button.setCheckable(True)
        self.auto_run_interval = QLineEdit("1000")
        self.auto_run_command = QLineEdit(":val? 1")
        automation_layout.addWidget(self.auto_run_button, 0, 0)
        automation_layout.addWidget(QLabel("Interval (ms):"), 0, 1)
        automation_layout.addWidget(self.auto_run_interval, 0, 2)
        automation_layout.addWidget(QLabel("Command:"), 1, 0)
        automation_layout.addWidget(self.auto_run_command, 1, 1, 1, 2)
        automation_group.setLayout(automation_layout)

        main_layout.addWidget(view_group)
        main_layout.addWidget(automation_group)
        main_layout.addStretch(1)

        top_level_layout.addLayout(main_layout)
        top_level_layout.addStretch(1)
           