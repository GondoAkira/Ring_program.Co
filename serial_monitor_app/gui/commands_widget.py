from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QHBoxLayout
)
from PySide6.QtCore import Signal

class CommandsWidget(QWidget):
    """A widget to display and manage commands."""
    command_to_send = Signal(str)
    load_commands_requested = Signal()
    save_commands_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Command List Group ---
        cmd_list_group = QGroupBox("Command List")
        cmd_list_layout = QVBoxLayout()
        
        # File operations for commands
        cmd_file_layout = QHBoxLayout()
        self.load_cmds_button = QPushButton("Load from File...")
        self.save_cmds_button = QPushButton("Save to File...")
        cmd_file_layout.addWidget(self.load_cmds_button)
        cmd_file_layout.addWidget(self.save_cmds_button)
        cmd_list_layout.addLayout(cmd_file_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout(scroll_widget)
        self.command_entries = []
        for i in range(33):
            label = QLabel(f"CMD {i+1}:")
            line_edit = QLineEdit()
            send_button = QPushButton("Send")
            send_button.clicked.connect(lambda _, le=line_edit: self.send_command(le.text()))
            line_edit.returnPressed.connect(lambda le=line_edit: self.send_command(le.text()))
            self.grid_layout.addWidget(label, i, 0)
            self.grid_layout.addWidget(line_edit, i, 1)
            self.grid_layout.addWidget(send_button, i, 2)
            self.command_entries.append(line_edit)
        scroll_area.setWidget(scroll_widget)
        cmd_list_layout.addWidget(scroll_area)
        cmd_list_group.setLayout(cmd_list_layout)

        main_layout.addWidget(cmd_list_group)

        # --- Connect signals ---
        self.load_cmds_button.clicked.connect(self.load_commands_requested)
        self.save_cmds_button.clicked.connect(self.save_commands_requested)

    def send_command(self, command_text):
        if command_text:
            self.command_to_send.emit(command_text)