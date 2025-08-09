import numpy as np
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDoubleSpinBox, QLabel, QGroupBox, QPushButton
)
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from .matplotlib_widget import MatplotlibWidget

class BKGraphWindow(QMainWindow):
    """A window to display the 8-channel BK buffer graph with all controls."""
    closing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Err wave View")
        self.setGeometry(250, 250, 800, 700)

        self.original_data = None
        self.controls = {}
        self.is_autoscale = True
        self.num_channels = 8
        self.points_per_channel = 512

        # --- Main Layout ---
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # --- Graph Widget and Toolbar ---
        self.graph_widget = MatplotlibWidget()
        toolbar = NavigationToolbar2QT(self.graph_widget.canvas, self)
        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.graph_widget, 1)

        # --- Scale and Clear Controls ---
        scale_clear_group = QGroupBox("Display Controls")
        scale_clear_layout = QHBoxLayout()

        self.y_min_spinbox = QDoubleSpinBox()
        self.y_min_spinbox.setRange(-1e9, 1e9)
        self.y_max_spinbox = QDoubleSpinBox()
        self.y_max_spinbox.setRange(-1e9, 1e9)
        self.y_max_spinbox.setValue(5000)

        apply_scale_button = QPushButton("Apply Y-Scale")
        auto_scale_button = QPushButton("Auto Scale")
        clear_button = QPushButton("Clear Graph")

        scale_clear_layout.addWidget(QLabel("Y-Min:"))
        scale_clear_layout.addWidget(self.y_min_spinbox)
        scale_clear_layout.addWidget(QLabel("Y-Max:"))
        scale_clear_layout.addWidget(self.y_max_spinbox)
        scale_clear_layout.addWidget(apply_scale_button)
        scale_clear_layout.addWidget(auto_scale_button)
        scale_clear_layout.addStretch(1)
        scale_clear_layout.addWidget(clear_button)
        scale_clear_group.setLayout(scale_clear_layout)
        main_layout.addWidget(scale_clear_group)

        # --- Channel Controls ---
        controls_group = QGroupBox("Channel Controls")
        controls_layout = QHBoxLayout()
        
        for i in range(self.num_channels):
            ch_layout = QVBoxLayout()
            ch_label = QLabel(f"Channel {i+1}")
            ch_label.setAlignment(Qt.AlignCenter)
            
            gain_layout = QHBoxLayout()
            gain_label = QLabel("Gain:")
            gain_spinbox = QDoubleSpinBox()
            gain_spinbox.setRange(-1000.0, 1000.0)
            gain_spinbox.setValue(1.0)
            gain_spinbox.setDecimals(4)
            gain_spinbox.setSingleStep(0.1)
            gain_layout.addWidget(gain_label)
            gain_layout.addWidget(gain_spinbox)
            
            offset_layout = QHBoxLayout()
            offset_label = QLabel("Offset:")
            offset_spinbox = QDoubleSpinBox()
            offset_spinbox.setRange(-10000.0, 10000.0)
            offset_spinbox.setValue(0.0)
            offset_spinbox.setDecimals(4)
            offset_spinbox.setSingleStep(1.0)
            offset_layout.addWidget(offset_label)
            offset_layout.addWidget(offset_spinbox)

            self.controls[i] = {'gain': gain_spinbox, 'offset': offset_spinbox}

            gain_spinbox.valueChanged.connect(self.apply_and_redraw)
            offset_spinbox.valueChanged.connect(self.apply_and_redraw)

            ch_layout.addWidget(ch_label)
            ch_layout.addLayout(gain_layout)
            ch_layout.addLayout(offset_layout)
            controls_layout.addLayout(ch_layout)

        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group, 0)

        # --- Connect signals ---
        apply_scale_button.clicked.connect(self.apply_y_scale)
        auto_scale_button.clicked.connect(self.enable_auto_scale)
        clear_button.clicked.connect(self.clear_graph)

    def update_and_plot(self, original_data):
        self.original_data = original_data.copy()
        self.apply_and_redraw()

    def apply_and_redraw(self):
        if self.original_data is None:
            return

        processed_data = self.original_data.copy()

        for i in range(self.num_channels):
            gain = self.controls[i]['gain'].value()
            offset = self.controls[i]['offset'].value()
            start_index = i * self.points_per_channel
            end_index = start_index + self.points_per_channel
            processed_data[start_index:end_index] = self.original_data[start_index:end_index] * gain + offset

        self.graph_widget.plot_data(processed_data, num_channels=self.num_channels, points_per_channel=self.points_per_channel)
        if not self.is_autoscale:
            self.apply_y_scale()

    def apply_y_scale(self):
        self.is_autoscale = False
        y_min = self.y_min_spinbox.value()
        y_max = self.y_max_spinbox.value()
        self.graph_widget.axes.set_ylim(y_min, y_max)
        self.graph_widget.canvas.draw()

    def enable_auto_scale(self):
        self.is_autoscale = True
        self.graph_widget.axes.autoscale(enable=True, axis='y')
        self.apply_and_redraw()

    def clear_graph(self):
        self.original_data = None
        self.graph_widget.axes.clear()
        self.graph_widget.axes.grid(True, which='both', linestyle='--', linewidth=0.5)
        self.graph_widget.canvas.draw()

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)