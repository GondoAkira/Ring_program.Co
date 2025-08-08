from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QScrollArea, QLabel, QLineEdit, 
    QGroupBox
)
from PySide6.QtCore import Qt, QEvent
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

        main_layout.addWidget(values_group)

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

    def closeEvent(self, event):
        """Handle window close event."""
        super().closeEvent(event)

    def get_all_labels(self):
        return [self.value_labels[i].text() for i in range(60)]

    def get_all_values(self):
        return [self.value_line_edits[i].text() for i in range(60)]

    def get_right_column_labels(self):
        return [self.value_labels[i].text() for i in range(45, 60)]

    def get_right_column_values(self):
        return [self.value_line_edits[i].text() for i in range(45, 60)]