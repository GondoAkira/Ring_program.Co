import csv
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QFileDialog, QRadioButton, QButtonGroup
)
from PySide6.QtCore import QTimer, Qt, QEvent
from PySide6.QtGui import QFont

class ValueWindow(QWidget):
    """A separate window to display PI values and handle logging."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PI Values Display")
        self.setWindowFlags(self.windowFlags() | Qt.Window)

        # --- Data Storage ---
        self.value_labels = {}
        self.value_line_edits = {}
        self.log_timer = QTimer(self)
        self.log_file_path = ""
        self.current_font_size = 10

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)

        # --- Values Group ---
        values_group = QGroupBox("Real-time Values")
        values_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.installEventFilter(self)

        scroll_widget = QWidget()
        self.grid_layout = QGridLayout(scroll_widget)

        # Create 60 value entries in a 15x4 grid
        num_items = 60
        num_rows = 15
        initial_font = QFont()
        initial_font.setPointSize(self.current_font_size)

        for i in range(num_items):
            row = i % num_rows
            col = i // num_rows
            num = i + 1
            label = QLabel(f"Value {num}:")
            line_edit = QLineEdit()
            line_edit.setReadOnly(True)
            label.setFont(initial_font)
            line_edit.setFont(initial_font)
            self.grid_layout.addWidget(label, row, col * 2)
            self.grid_layout.addWidget(line_edit, row, col * 2 + 1)
            self.value_labels[i] = label
            self.value_line_edits[i] = line_edit

        scroll_area.setWidget(scroll_widget)
        values_layout.addWidget(scroll_area)
        values_group.setLayout(values_layout)

        # --- Logging Group ---
        logging_group = QGroupBox("Logging")
        logging_layout = QGridLayout()
        self.log_start_button = QPushButton("Start Logging")
        self.log_stop_button = QPushButton("Stop Logging")
        self.log_stop_button.setEnabled(False)
        self.log_status_label = QLabel("Status: Idle")
        self.log_file_label = QLineEdit()
        self.log_file_label.setReadOnly(True)
        self.log_file_label.setPlaceholderText("Log file path...")

        # ロギング対象選択
        self.radio_all = QRadioButton("全60個")
        self.radio_right = QRadioButton("右端15個のみ")
        self.radio_all.setChecked(True)
        self.log_radio_group = QButtonGroup()
        self.log_radio_group.addButton(self.radio_all)
        self.log_radio_group.addButton(self.radio_right)

        logging_layout.addWidget(self.log_start_button, 0, 0)
        logging_layout.addWidget(self.log_stop_button, 0, 1)
        logging_layout.addWidget(QLabel("File:"), 1, 0)
        logging_layout.addWidget(self.log_file_label, 1, 1)
        logging_layout.addWidget(self.radio_all, 2, 0)
        logging_layout.addWidget(self.radio_right, 2, 1)
        logging_layout.addWidget(self.log_status_label, 3, 0, 1, 2)
        logging_group.setLayout(logging_layout)

        main_layout.addWidget(values_group)
        main_layout.addWidget(logging_group)

        # --- Connect signals ---
        self.log_start_button.clicked.connect(self.start_logging)
        self.log_stop_button.clicked.connect(self.stop_logging)
        self.log_timer.timeout.connect(self.log_current_values)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Wheel and event.modifiers() == Qt.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self.zoom(1.1)  # Zoom in
            else:
                self.zoom(0.9)  # Zoom out
            return True  # Event handled
        return super().eventFilter(source, event)

    def zoom(self, factor):
        self.current_font_size *= factor
        # Add limits to font size
        if self.current_font_size < 4:
            self.current_font_size = 4
        elif self.current_font_size > 50:
            self.current_font_size = 50

        font = QFont()
        font.setPointSize(int(self.current_font_size))
        for i in range(len(self.value_labels)):
            self.value_labels[i].setFont(font)
            self.value_line_edits[i].setFont(font)

    def update_value(self, index, value):
        """Slot to update a specific value in the grid."""
        if index in self.value_line_edits:
            self.value_line_edits[index].setText(str(value))

    def start_logging(self):
        default_filename = f"C:\\temp\\VBdata\\LOGDATA-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log File", default_filename, "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return

        self.log_file_path = file_path
        self.log_file_label.setText(file_path)
        try:
            with open(self.log_file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                if self.radio_right.isChecked():
                    header = ["Timestamp"] + [self.value_labels[i].text() for i in range(45, 60)]
                else:
                    header = ["Timestamp"] + [self.value_labels[i].text() for i in range(60)]
                writer.writerow(header)
        except Exception as e:
            self.log_status_label.setText(f"Error: {e}")
            return

        self.log_timer.start(1000) # Log every 1 second
        self.log_start_button.setEnabled(False)
        self.log_stop_button.setEnabled(True)
        self.log_status_label.setText("Status: Logging...")

    def stop_logging(self):
        self.log_timer.stop()
        self.log_start_button.setEnabled(True)
        self.log_stop_button.setEnabled(False)
        self.log_status_label.setText(f"Status: Stopped. Saved to {self.log_file_path}")

    def log_current_values(self):
        if not self.log_file_path:
            return
        try:
            with open(self.log_file_path, 'a', newline='') as f:
                writer = csv.writer(f)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if self.radio_right.isChecked():
                    values = [self.value_line_edits[i].text() for i in range(45, 60)]
                else:
                    values = [self.value_line_edits[i].text() for i in range(60)]
                writer.writerow([timestamp] + values)
        except Exception as e:
            self.log_status_label.setText(f"Error: {e}")
            self.stop_logging()

    def closeEvent(self, event):
        """Ensure logging is stopped when the window is closed."""
        self.stop_logging()
        super().closeEvent(event)