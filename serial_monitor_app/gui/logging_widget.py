import os
import csv
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
    QFileDialog, QRadioButton, QButtonGroup
)
from PySide6.QtCore import QTimer, Signal

class LoggingWidget(QWidget):
    logging_status_changed = Signal()

    def __init__(self, value_window, parent=None):
        super().__init__(parent)
        self.value_window = value_window
        self.log_timer = QTimer(self)
        self.log_file_path = ""
        self.is_logging = False

        main_layout = QVBoxLayout(self)
        logging_group = QGroupBox("Logging")
        logging_layout = QGridLayout()

        self.folder_label = QLineEdit()
        self.folder_label.setReadOnly(True)
        self.folder_btn = QPushButton("保存先選択")
        self.filename_edit = QLineEdit(f"log_{datetime.now():%Y%m%d_%H%M%S}.csv")

        logging_layout.addWidget(QLabel("保存先:"), 0, 0)
        logging_layout.addWidget(self.folder_label, 0, 1)
        logging_layout.addWidget(self.folder_btn, 0, 2)
        logging_layout.addWidget(QLabel("ファイル名:"), 1, 0)
        logging_layout.addWidget(self.filename_edit, 1, 1, 1, 2)

        # Logging target selection
        self.radio_all = QRadioButton("全60個")
        self.radio_right = QRadioButton("右端15個のみ")
        self.radio_all.setChecked(True)
        self.log_radio_group = QButtonGroup()
        self.log_radio_group.addButton(self.radio_all)
        self.log_radio_group.addButton(self.radio_right)
        logging_layout.addWidget(self.radio_all, 2, 0)
        logging_layout.addWidget(self.radio_right, 2, 1)

        self.start_btn = QPushButton("測定開始")
        self.stop_btn = QPushButton("測定停止")
        self.stop_btn.setEnabled(False)
        self.init_btn = QPushButton("初期化")

        logging_layout.addWidget(self.start_btn, 3, 0)
        logging_layout.addWidget(self.stop_btn, 3, 1)
        logging_layout.addWidget(self.init_btn, 3, 2)

        self.log_status_label = QLabel("Status: Idle")
        logging_layout.addWidget(self.log_status_label, 4, 0, 1, 3)

        logging_group.setLayout(logging_layout)
        main_layout.addWidget(logging_group)

        self.folder_btn.clicked.connect(self.select_folder)
        self.start_btn.clicked.connect(self.start_logging)
        self.stop_btn.clicked.connect(self.stop_logging)
        self.init_btn.clicked.connect(self.initialize_device)
        self.log_timer.timeout.connect(self.log_current_values)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "保存先フォルダを選択")
        if folder:
            self.folder_label.setText(folder)

    def start_logging(self):
        folder = self.folder_label.text()
        filename = self.filename_edit.text()
        if not folder or not filename:
            self.log_status_label.setText("保存先とファイル名を指定してください")
            return
        self.log_file_path = os.path.join(folder, filename)
        try:
            with open(self.log_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if self.radio_right.isChecked():
                    header = ["Timestamp"] + self.value_window.get_right_column_labels()
                else:
                    header = ["Timestamp"] + self.value_window.get_all_labels()
                writer.writerow(header)
        except Exception as e:
            self.log_status_label.setText(f"Error: {e}")
            return
        self.is_logging = True
        self.log_timer.start(1000)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_status_label.setText("Status: Logging...")
        self.logging_status_changed.emit()

    def stop_logging(self):
        self.log_timer.stop()
        self.is_logging = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_status_label.setText(f"Status: Stopped. Saved to {self.log_file_path}")
        self.logging_status_changed.emit()

    def log_current_values(self):
        if not self.log_file_path:
            return
        try:
            with open(self.log_file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if self.radio_right.isChecked():
                    values = self.value_window.get_right_column_values()
                else:
                    values = self.value_window.get_all_values()
                writer.writerow([timestamp] + values)
        except Exception as e:
            self.log_status_label.setText(f"Error: {e}")
            self.stop_logging()

    def initialize_device(self):
        self.log_status_label.setText("初期化コマンド送信（実装例）")