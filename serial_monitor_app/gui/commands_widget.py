import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QHBoxLayout, QFileDialog, QTextEdit, QProgressBar
)
from PySide6.QtCore import Signal, Qt, QTimer

class CommandsWidget(QWidget):
    """A widget to display and manage commands and EEPROM operations."""
    command_to_send = Signal(str)
    eeprom_read_started = Signal()
    eeprom_process_finished = Signal()
    load_commands_requested = Signal()
    save_commands_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
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

        # --- EEPROM Operations Group ---
        eeprom_group = QGroupBox("EEPROM Operations")
        eeprom_layout = QGridLayout()
        self.start_addr_box = QLineEdit("0")
        self.end_addr_box = QLineEdit("1023")
        self.filename_box = QLineEdit("eeprom_dump.json")
        self.rom_to_file_button = QPushButton("ROM -> File")
        self.file_to_rom_button = QPushButton("File -> ROM")
        self.cancel_button = QPushButton("Cancel")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)

        self.eeprom_result_box = QTextEdit()
        self.eeprom_result_box.setReadOnly(True)
        self.eeprom_result_box.setPlaceholderText("EEPROM operation results...")

        eeprom_layout.addWidget(QLabel("Start Addr:"), 0, 0)
        eeprom_layout.addWidget(self.start_addr_box, 0, 1)
        eeprom_layout.addWidget(QLabel("End Addr:"), 1, 0)
        eeprom_layout.addWidget(self.end_addr_box, 1, 1)
        eeprom_layout.addWidget(QLabel("Filename:"), 2, 0)
        eeprom_layout.addWidget(self.filename_box, 2, 1)
        eeprom_layout.addWidget(self.rom_to_file_button, 3, 0)
        eeprom_layout.addWidget(self.file_to_rom_button, 3, 1)
        eeprom_layout.addWidget(self.cancel_button, 4, 0, 1, 2)
        eeprom_layout.addWidget(self.progress_bar, 5, 0, 1, 2)
        eeprom_layout.addWidget(self.eeprom_result_box, 6, 0, 1, 2)
        eeprom_group.setLayout(eeprom_layout)

        # Set stretch factor to make command list wider than EEPROM section
        main_layout.addWidget(cmd_list_group, 2)
        main_layout.addWidget(eeprom_group, 1)

        # --- Timers and State for Async Operations ---
        self.eeprom_timer = QTimer(self)
        self.eeprom_timer.setInterval(100) # 100 ms delay between commands
        self.eeprom_read_buffer = {}
        self.eeprom_write_lines = []
        self.current_write_index = 0

        # --- Connect signals ---
        self.rom_to_file_button.clicked.connect(self.start_rom_to_file)
        self.file_to_rom_button.clicked.connect(self.start_file_to_rom)
        self.eeprom_timer.timeout.connect(self.process_eeprom_step)
        self.load_cmds_button.clicked.connect(self.load_commands_requested)
        self.save_cmds_button.clicked.connect(self.save_commands_requested)

    def send_command(self, command_text):
        if command_text:
            self.command_to_send.emit(command_text)

    def start_rom_to_file(self):
        try:
            self.start_addr = int(self.start_addr_box.text())
            self.end_addr = int(self.end_addr_box.text())
            self.current_addr = self.start_addr
            self.eeprom_read_buffer.clear()
            self.eeprom_result_box.clear()
            self.eeprom_result_box.append(f"Starting ROM to File from {self.start_addr} to {self.end_addr}...")
            self.eeprom_read_started.emit()
            self.eeprom_timer.start()
        except ValueError:
            self.eeprom_result_box.setText("Error: Invalid start/end address.")

    def start_file_to_rom(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load EEPROM File", "", "JSON files (*.json);;Text files (*.txt);;All Files (*)")
        if not file_path:
            return
        try:
            _, ext = os.path.splitext(file_path)
            if ext == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.eeprom_write_lines = data.get("eeprom_data", [])
            elif ext == '.txt':
                with open(file_path, 'r') as f:
                    self.eeprom_write_lines = [line.strip() for line in f if line.strip()]
            else:
                self.eeprom_result_box.setText(f"Unsupported file type: {ext}")
                return

            self.current_write_index = 0
            self.eeprom_result_box.clear()
            self.eeprom_result_box.append(f"Starting File to ROM from {file_path}...")
            self.eeprom_timer.start()
        except Exception as e:
            self.eeprom_result_box.setText(f"Error loading file: {e}")

    def process_eeprom_step(self):
        # ROM -> File processing
        if hasattr(self, 'current_addr') and self.current_addr <= self.end_addr:
            command = f":mem? {self.current_addr}"
            self.command_to_send.emit(command)
            self.current_addr += 1
            if self.current_addr > self.end_addr:
                self.eeprom_timer.stop()
                # Give last command time to be received before saving
                QTimer.singleShot(500, self.save_rom_data)
        # File -> ROM processing
        elif self.current_write_index < len(self.eeprom_write_lines):
            line = self.eeprom_write_lines[self.current_write_index]
            command = f":mem {line}"
            self.command_to_send.emit(command)
            self.eeprom_result_box.append(f"Sent: {command}")
            self.current_write_index += 1
            if self.current_write_index >= len(self.eeprom_write_lines):
                self.eeprom_timer.stop()
                self.eeprom_result_box.append("--- File to ROM finished ---")
                self.eeprom_process_finished.emit()
                self.eeprom_write_lines.clear() # Clear after finishing

    def append_to_read_buffer(self, data):
        # Only append if the timer is active (i.e., a read is in progress)
        if self.eeprom_timer.isActive() and hasattr(self, 'current_addr'):
            # Assuming data is in "address=value" format
            try:
                addr, value = data.split('=')
                self.eeprom_read_buffer[int(addr)] = value.strip()
                self.eeprom_result_box.append(data)
            except ValueError:
                self.eeprom_result_box.append(f"Unrecognized format: {data}")

    def save_rom_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save EEPROM Data", self.filename_box.text(), "JSON files (*.json);;Text files (*.txt);;All Files (*)")
        if not file_path:
            self.eeprom_result_box.append("--- ROM to File cancelled by user. ---")
            self.eeprom_process_finished.emit()
            return
            
        try:
            _, ext = os.path.splitext(file_path)
            with open(file_path, 'w') as f:
                if ext == '.json':
                    json.dump({"eeprom_data": self.eeprom_read_buffer}, f, indent=4)
                else: # Default to text
                    f.write('\n'.join([f"{k}={v}" for k, v in sorted(self.eeprom_read_buffer.items())]))
            self.eeprom_result_box.append(f"--- ROM to File finished. Saved to {file_path} ---")
        except Exception as e:
            self.eeprom_result_box.append(f"Error saving file: {e}")
        finally:
            self.eeprom_process_finished.emit()
            self.eeprom_read_buffer.clear() # Clear after finishing
            del self.current_addr # End the read state
