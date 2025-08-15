import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit,
    QGroupBox, QFileDialog, QTextEdit, QProgressBar
)
from PySide6.QtCore import Signal, QTimer, Qt

class EEPROMWindow(QWidget):
    command_to_send = Signal(str)
    eeprom_read_started = Signal()
    eeprom_process_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EEPROM Operations")
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.setGeometry(300, 300, 400, 400)

        main_layout = QVBoxLayout(self)

        # --- EEPROM Operations Group ---
        eeprom_group = QGroupBox("EEPROM 読み書き")
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
        self.eeprom_result_box.setFixedHeight(100)

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
        main_layout.addWidget(eeprom_group)

        # --- Timers and State for Async Operations ---
        self.eeprom_timer = QTimer(self)
        self.eeprom_timer.setInterval(100)
        self.read_buffer = {}
        self.write_lines = []
        self.current_write_index = 0

        # --- Connect signals ---
        self.rom_to_file_button.clicked.connect(self.start_rom_to_file)
        self.file_to_rom_button.clicked.connect(self.start_file_to_rom)
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.eeprom_timer.timeout.connect(self.process_eeprom_step)

    def start_rom_to_file(self):
        try:
            self.start_addr = int(self.start_addr_box.text())
            self.end_addr = int(self.end_addr_box.text())
            self.current_addr = self.start_addr
            self.read_buffer.clear()
            self.eeprom_result_box.clear()
            self.eeprom_result_box.append(f"Starting ROM to File from {self.start_addr} to {self.end_addr}...")
            self.progress_bar.setRange(0, self.end_addr - self.start_addr)
            self.progress_bar.setValue(0)
            self.eeprom_read_started.emit()
            self.eeprom_timer.start()
        except ValueError:
            self.eeprom_result_box.setText("Error: Invalid start/end address.")

    def start_file_to_rom(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load EEPROM File", "", "JSON files (*.json);;Text files (*.txt);;All Files (*)")
        if not file_path: return
        try:
            _, ext = os.path.splitext(file_path)
            if ext == '.json':
                with open(file_path, 'r') as f: self.write_lines = json.load(f).get("eeprom_data", [])
            elif ext == '.txt':
                with open(file_path, 'r') as f: self.write_lines = [line.strip() for line in f if line.strip()]
            else:
                self.eeprom_result_box.setText(f"Unsupported file type: {ext}"); return
            self.current_write_index = 0
            self.eeprom_result_box.clear()
            self.eeprom_result_box.append(f"Starting File to ROM from {file_path}...")
            self.progress_bar.setRange(0, len(self.write_lines))
            self.progress_bar.setValue(0)
            self.eeprom_timer.start()
        except Exception as e:
            self.eeprom_result_box.setText(f"Error loading file: {e}")

    def process_eeprom_step(self):
        if hasattr(self, 'current_addr') and self.current_addr <= self.end_addr:
            self.command_to_send.emit(f":mem? {self.current_addr}")
            self.progress_bar.setValue(self.current_addr - self.start_addr)
            self.current_addr += 1
            if self.current_addr > self.end_addr:
                self.eeprom_timer.stop()
                QTimer.singleShot(500, self.save_rom_data)
        elif self.current_write_index < len(self.write_lines):
            line = self.write_lines[self.current_write_index]
            self.command_to_send.emit(f":mem {line}")
            self.eeprom_result_box.append(f"Sent: :mem {line}")
            self.progress_bar.setValue(self.current_write_index + 1)
            self.current_write_index += 1
            if self.current_write_index >= len(self.write_lines):
                self.eeprom_timer.stop()
                self.eeprom_result_box.append("--- File to ROM finished ---")
                self.eeprom_process_finished.emit()
                self.write_lines.clear()

    def append_to_read_buffer(self, data):
        if self.eeprom_timer.isActive() and hasattr(self, 'current_addr'):
            try:
                addr, value = data.split('=')
                self.read_buffer[int(addr)] = value.strip()
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
                if ext == '.json': json.dump({"eeprom_data": self.read_buffer}, f, indent=4)
                else: f.write('\n'.join([f"{k}={v}" for k, v in sorted(self.read_buffer.items())]))
            self.eeprom_result_box.append(f"--- ROM to File finished. Saved to {file_path} ---")
        except Exception as e: self.eeprom_result_box.append(f"Error saving file: {e}")
        finally:
            self.eeprom_process_finished.emit()
            self.read_buffer.clear()
            del self.current_addr

    def cancel_operation(self):
        if self.eeprom_timer.isActive():
            self.eeprom_timer.stop()
            self.eeprom_result_box.append("--- Operation Cancelled by User ---")
            self.eeprom_process_finished.emit()
            self.read_buffer.clear()
            self.write_lines.clear()
            if hasattr(self, 'current_addr'): del self.current_addr

    def closeEvent(self, event):
        self.cancel_operation()
        super().closeEvent(event)