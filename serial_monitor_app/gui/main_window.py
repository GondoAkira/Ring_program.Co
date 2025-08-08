# c:\Users\81804\Documents\0.lab-project\A program of Serial.exe from Mr. Tatsuno in TSC 20250730\serial_monitor_app\gui\main_window.py の修正例

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout # 必要なものをインポート
from .graph_widget import MplGraphWidget # 作成したグラフウィジェットをインポート

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Monitor with Graph")
        
        # ... (既存の初期化処理) ...

        # メインのウィジェットとレイアウトを設定
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # 例としてQVBoxLayoutを使用

        # ... (他のウィジェットの追加) ...

        # グラフウィジェットを作成してレイアウトに追加
        self.graph_widget = MplGraphWidget()
        main_layout.addWidget(self.graph_widget)

        # ... (他のウィジェットの追加) ...

        # シリアルデータ受信時などにグラフを更新する
        # self.serial_thread.data_received.connect(self.update_graph_data)

    # def update_graph_data(self, new_x, new_y):
    #     """シリアルデータ受信などでグラフを更新するためのメソッド（例）"""
    #     self.graph_widget.update_plot(new_x, new_y)

import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QMessageBox, QFileDialog, QComboBox, QStatusBar, QGroupBox
)
from datetime import datetime
from PySide6.QtCore import QTimer, QEvent, Qt, QSettings
from PySide6.QtGui import QIntValidator

from utils.serial_handler import SerialHandler
from utils.data_processor import DataProcessor
from gui.commands_widget import CommandsWidget
from gui.value_window import ValueWindow
from gui.graph_window import GraphWindow
from gui.connection_widget import ConnectionWidget
from gui.control_widget import ControlWidget
from gui.log_widget import LogWidget
from gui.logging_widget import LoggingWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Monitor")
        # ステータスバーを初期化
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        # ステータスバーに表示するラベルを作成
        self.status_connection_label = QLabel("Disconnected")
        self.status_activity_label = QLabel("Idle")
        self.statusBar.addPermanentWidget(self.status_connection_label)
        self.statusBar.addPermanentWidget(self.status_activity_label)
        self.setGeometry(100, 100, 500, 700)

        self.serial_handler = SerialHandler()
        self.data_processor = DataProcessor()
        self.auto_run_timer = QTimer(self)
        self.value_window = ValueWindow()
        self.graph_window = GraphWindow()
        self.is_eeprom_reading = False
        self.command_history = []
        self.settings = QSettings("YourCompany", "SerialMonitorApp")
        self.history_index = 0

        # --- Central Widget and Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.connection_widget = ConnectionWidget()
        self.control_widget = ControlWidget()
        self.log_widget = LogWidget()
        self.commands_widget = CommandsWidget()
        self.logging_widget = LoggingWidget(self.value_window)

        # Top horizontal layout for controls and logging
        top_controls_layout = QHBoxLayout()
        top_controls_layout.addWidget(self.control_widget)
        top_controls_layout.addWidget(self.logging_widget)

        # Bottom horizontal layout for the main work area (log and commands)
        main_work_area_layout = QHBoxLayout()
        # Give the log widget more horizontal space (stretch factor 2)
        main_work_area_layout.addWidget(self.log_widget, 2)
        # Give the commands widget less horizontal space (stretch factor 1)
        main_work_area_layout.addWidget(self.commands_widget, 1)

        main_layout.addWidget(self.connection_widget)
        main_layout.addLayout(top_controls_layout)
        main_layout.addLayout(main_work_area_layout)

        # --- Set Validators ---
        self.control_widget.auto_run_interval.setValidator(QIntValidator(1, 600000)) # 1ms to 10min
        main_layout.setStretch(2, 1) # Make the main work area expand vertically

        # --- Connect signals and slots ---
        self.connection_widget.open_button.clicked.connect(self.open_port)
        self.connection_widget.close_button.clicked.connect(self.close_port)
        self.connection_widget.com_port_combo.mousePressEvent = self.refresh_ports_on_click
        
        self.control_widget.auto_run_button.toggled.connect(self.toggle_auto_run)
        self.control_widget.show_values_button.clicked.connect(self.value_window.show)
        self.control_widget.show_graph_button.clicked.connect(self.graph_window.show)

        self.log_widget.send_button.clicked.connect(self.send_main_command)
        self.log_widget.clear_button.clicked.connect(self.log_widget.receive_textbox.clear)

        self.auto_run_timer.timeout.connect(self.execute_auto_run_command)

        self.serial_handler.port_opened.connect(self.on_port_opened)
        self.serial_handler.port_closed.connect(self.on_port_closed)
        self.serial_handler.port_error.connect(self.on_port_error)
        self.serial_handler.data_received.connect(self.route_received_data)

        self.data_processor.parsing_error.connect(self.on_data_received)
        self.data_processor.mem_data_updated.connect(self.update_graph)
        self.data_processor.pi_data_updated.connect(self.value_window.update_value)
        
        self.commands_widget.command_to_send.connect(self.send_data)
        self.commands_widget.eeprom_read_started.connect(self.handle_eeprom_read_start)
        self.commands_widget.eeprom_process_finished.connect(self.handle_eeprom_process_finish)
        self.commands_widget.load_commands_requested.connect(self.load_commands_from_file)
        self.commands_widget.save_commands_requested.connect(self.save_commands_to_file)
        self.logging_widget.logging_status_changed.connect(self.update_activity_label)

        self.log_widget.send_textbox.installEventFilter(self)
        self.load_initial_settings()
        self.restore_settings()
        self.statusBar.showMessage("Ready", 3000)

    def load_initial_settings(self):
        config_path_json = os.path.join(os.path.dirname(__file__), '..', 'config', 'init_load_cmd.json')
        config_path_txt = os.path.join(os.path.dirname(__file__), '..', 'config', 'init_load_cmd.txt')
        if os.path.exists(config_path_json):
            self.load_commands(config_path_json, silent=True)
        elif os.path.exists(config_path_txt):
            self.load_commands(config_path_txt, silent=True)

    def load_commands_from_file(self):
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Commands File", config_dir, "JSON files (*.json);;Text files (*.txt);;All Files (*)")
        if file_path:
            self.load_commands(file_path)

    def save_commands_to_file(self):
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Commands File", config_dir, "JSON files (*.json);;All Files (*)")
        if not file_path:
            return

        try:
            data = {
                "commands": [self.commands_widget.command_entries[i].text() for i in range(33)],
                "labels": [self.value_window.value_labels[i].text() for i in range(60)]
            }
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            self.log_widget.receive_textbox.append(f"--- Commands saved to {os.path.basename(file_path)} ---")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save commands file: {e}")

    def load_commands(self, file_path, silent=False):
        try:
            _, ext = os.path.splitext(file_path)
            if ext == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                commands = data.get("commands", [])
                labels = data.get("labels", [])
            elif ext == '.txt':
                with open(file_path, 'r') as f:
                    lines = [line.strip() for line in f.readlines()]
                commands = lines[:33]
                labels = lines[33:93]
            else:
                if not silent:
                    QMessageBox.warning(self, "Unsupported File", f"Unsupported file type: {ext}")
                return

            # Load commands
            for i, text in enumerate(commands):
                if i < len(self.commands_widget.command_entries):
                    self.commands_widget.command_entries[i].setText(text)
            
            # Load labels
            for i, text in enumerate(labels):
                if i in self.value_window.value_labels:
                    self.value_window.value_labels[i].setText(text)
            
            if not silent:
                self.log_widget.receive_textbox.append(f"--- Commands loaded from {os.path.basename(file_path)} ---")

        except FileNotFoundError:
            if not silent:
                QMessageBox.warning(self, "Not Found", f"Configuration file not found: {os.path.basename(file_path)}")
        except Exception as e:
            if not silent:
                QMessageBox.critical(self, "Error", f"Failed to load commands file: {e}")

    def route_received_data(self, data):
        # Add a timestamp to all incoming data and log it.
        timestamp = datetime.now().strftime("[%H:%M:%S.%f]")[:-3]
        self.log_widget.receive_textbox.append(f"{timestamp} {data}")

        if self.is_eeprom_reading:
            self.commands_widget.append_to_read_buffer(data)
        else:
            self.data_processor.process_line(data)

    def handle_eeprom_read_start(self):
        self.is_eeprom_reading = True
        self.log_widget.receive_textbox.append("--- EEPROM Read Mode ON ---")
        self.update_activity_label()

    def handle_eeprom_process_finish(self):
        self.is_eeprom_reading = False
        self.log_widget.receive_textbox.append("--- EEPROM Read Mode OFF ---")
        self.update_activity_label()

    def refresh_ports(self):
        self.connection_widget.com_port_combo.clear()
        ports = self.serial_handler.get_available_ports()
        self.connection_widget.com_port_combo.addItems(ports)

    def refresh_ports_on_click(self, event):
        self.refresh_ports()
        QComboBox.mousePressEvent(self.connection_widget.com_port_combo, event)

    def open_port(self):
        port = self.connection_widget.com_port_combo.currentText()
        baudrate = self.connection_widget.baud_rate_combo.currentText()
        parity = self.connection_widget.parity_combo.currentText()
        if not port:
            self.on_port_error("Please select a COM port.")
            return
        self.statusBar.showMessage(f"Connecting to {port}...")
        self.serial_handler.open_port(port, baudrate, parity)

    def close_port(self):
        self.serial_handler.close_port()

    def send_main_command(self):
        data = self.log_widget.send_textbox.text()
        # Add to history if not empty and not a duplicate of the last command
        if data and (not self.command_history or self.command_history[-1] != data):
            self.command_history.append(data)
        # Reset history index to be at the end (for new typing)
        self.history_index = len(self.command_history)
        
        self.send_data(data)
        self.log_widget.send_textbox.clear()

    def send_data(self, data):
        if data and self.serial_handler.serial and self.serial_handler.serial.is_open:
            self.serial_handler.send_data(data)
        elif not self.serial_handler.serial or not self.serial_handler.serial.is_open:
            self.on_port_error("Port is not open.")

    def on_port_opened(self):
        self.connection_widget.open_button.setEnabled(False)
        self.connection_widget.close_button.setEnabled(True)
        self.connection_widget.com_port_combo.setEnabled(False)
        self.connection_widget.baud_rate_combo.setEnabled(False)
        self.connection_widget.parity_combo.setEnabled(False)
        self.log_widget.receive_textbox.append("--- Port Opened ---")
        port_name = self.serial_handler.serial.port
        self.status_connection_label.setText(f"Connected: {port_name}")
        self.statusBar.showMessage("Port opened successfully", 3000)

    def on_port_closed(self):
        self.connection_widget.open_button.setEnabled(True)
        self.connection_widget.close_button.setEnabled(False)
        self.connection_widget.com_port_combo.setEnabled(True)
        self.connection_widget.baud_rate_combo.setEnabled(True)
        self.connection_widget.parity_combo.setEnabled(True)
        self.log_widget.receive_textbox.append("--- Port Closed ---")
        if self.control_widget.auto_run_button.isChecked():
            self.control_widget.auto_run_button.setChecked(False)
        self.status_connection_label.setText("Disconnected")        
        self.update_activity_label()
        self.statusBar.showMessage("Port closed", 3000)

    def on_port_error(self, message):
        QMessageBox.critical(self, "Serial Port Error", message)
        self.status_connection_label.setText("Error")
        self.statusBar.showMessage(message, 5000)

    def on_data_received(self, data):
        # This now primarily handles parsing errors from the DataProcessor.
        timestamp = datetime.now().strftime("[%H:%M:%S.%f]")[:-3]
        self.log_widget.receive_textbox.append(f"{timestamp} {data}")

    def update_graph(self):
        self.graph_window.update_plot(self.data_processor.mem_buf)

    def toggle_auto_run(self, checked):
        if checked:
            if not self.serial_handler.serial or not self.serial_handler.serial.is_open:
                self.on_port_error("Cannot start Auto Run: Port is not open.")
                self.control_widget.auto_run_button.setChecked(False)
                return
            try:
                interval = int(self.control_widget.auto_run_interval.text())
                self.auto_run_timer.start(interval)
                self.control_widget.auto_run_button.setText("Stop")
            except ValueError:
                self.on_port_error("Invalid interval. Please enter a number.")
                self.control_widget.auto_run_button.setChecked(False)
        else:
            self.auto_run_timer.stop()
            self.control_widget.auto_run_button.setText("Auto Run")
        self.update_activity_label()

    def update_activity_label(self):
        """Updates the activity status label based on the application state priority."""
        if self.is_eeprom_reading:
            self.status_activity_label.setText("EEPROM Reading...")
        elif self.logging_widget.is_logging:
            self.status_activity_label.setText("Logging...")
        elif self.control_widget.auto_run_button.isChecked():
            self.status_activity_label.setText("Auto Run Active")
        else:
            self.status_activity_label.setText("Idle")

    def execute_auto_run_command(self):
        command = self.control_widget.auto_run_command.text()
        self.send_data(command)

    def restore_settings(self):
        """Restore window geometry and connection settings."""
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        
        self.refresh_ports() # Load available ports first
        
        # Restore connection settings
        port = self.settings.value("port", "")
        if port and self.connection_widget.com_port_combo.findText(port) != -1:
            self.connection_widget.com_port_combo.setCurrentText(port)
        self.connection_widget.baud_rate_combo.setCurrentText(self.settings.value("baudrate", "9600"))
        self.connection_widget.parity_combo.setCurrentText(self.settings.value("parity", "None"))

    def closeEvent(self, event):
        """Save settings on close."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("port", self.connection_widget.com_port_combo.currentText())
        self.settings.setValue("baudrate", self.connection_widget.baud_rate_combo.currentText())
        self.settings.setValue("parity", self.connection_widget.parity_combo.currentText())
        self.value_window.close()
        self.graph_window.close()
        self.close_port()
        event.accept()

    def navigate_history(self, direction):
        """Navigate through command history."""
        if not self.command_history:
            return

        if direction == 0:  # Up
            if self.history_index > 0:
                self.history_index -= 1
        else:  # Down
            if self.history_index < len(self.command_history):
                self.history_index += 1

        if self.history_index < len(self.command_history):
            command = self.command_history[self.history_index]
            self.log_widget.send_textbox.setText(command)
            self.log_widget.send_textbox.end(False)
        else:
            self.log_widget.send_textbox.clear()

    def eventFilter(self, watched, event):
        if watched == self.log_widget.send_textbox and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                self.navigate_history(0)
                return True  # Event handled
            elif key == Qt.Key_Down:
                self.navigate_history(1)
                return True  # Event handled
        return super().eventFilter(watched, event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
