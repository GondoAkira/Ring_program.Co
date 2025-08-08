from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from .matplotlib_widget import MatplotlibWidget

class GraphWindow(QMainWindow):
    """A window to display the matplotlib graph."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graph View")
        self.setGeometry(200, 200, 800, 600)

        self.graph_widget = MatplotlibWidget()
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.graph_widget)
        self.setCentralWidget(central_widget)

    def update_plot(self, data):
        """Updates the plot with new data."""
        self.graph_widget.plot_data(data)
