from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MatplotlibWidget(QWidget):
    """A custom widget to embed a Matplotlib plot in a PySide6 application."""
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a Matplotlib figure and canvas
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        # The main axes for plotting
        self.axes = self.figure.add_subplot(111)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot_data(self, data_buffer, num_channels=4, points_per_channel=1024):
        """Clears the current plot and plots new data from the buffer."""
        self.axes.clear()

        colors = ['brown', 'red', 'orange', 'blue']

        for i in range(num_channels):
            start_index = i * points_per_channel
            end_index = start_index + points_per_channel
            channel_data = data_buffer[start_index:end_index]
            
            # Create x-axis values (0, 1, 2, ...)
            x_values = range(len(channel_data))

            self.axes.plot(x_values, channel_data, color=colors[i % len(colors)], linewidth=1)

        self.axes.grid(True, which='both', linestyle='--', linewidth=0.5)
        self.axes.set_title("Memory Buffer Data")
        self.axes.set_xlabel("Address")
        self.axes.set_ylabel("Value")
        self.canvas.draw()
