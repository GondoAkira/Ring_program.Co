import serial
import serial.tools.list_ports
from PySide6.QtCore import QObject, Signal, QThread

class SerialWorker(QObject):
    """Worker object that runs in a separate thread to read from serial port."""
    data_received = Signal(str)
    finished = Signal()

    def __init__(self, serial_instance):
        super().__init__()
        self.serial = serial_instance
        self._is_running = True

    def run(self):
        while self._is_running and self.serial and self.serial.is_open:
            try:
                line = self.serial.readline().decode('utf-8').strip()
                if line:
                    self.data_received.emit(line)
            except serial.SerialException:
                self._is_running = False
        self.finished.emit()

    def stop(self):
        self._is_running = False

class SerialHandler(QObject):
    """Handles all serial communication logic."""
    port_opened = Signal()
    port_closed = Signal()
    port_error = Signal(str)
    data_received = Signal(str)

    def __init__(self):
        super().__init__()
        self.serial = None
        self.thread = None
        self.worker = None

    @staticmethod
    def get_available_ports():
        """Returns a list of available COM ports."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def open_port(self, port, baudrate, parity_str):
        if self.serial and self.serial.is_open:
            self.port_error.emit("A port is already open.")
            return

        try:
            parity_map = {"None": serial.PARITY_NONE, "Odd": serial.PARITY_ODD, "Even": serial.PARITY_EVEN}
            self.serial = serial.Serial(
                port=port,
                baudrate=int(baudrate),
                parity=parity_map.get(parity_str, serial.PARITY_NONE),
                timeout=1
            )

            self.thread = QThread()
            self.worker = SerialWorker(self.serial)
            self.worker.moveToThread(self.thread)

            # Connect signals
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.data_received.connect(self.data_received)

            self.thread.start()
            self.port_opened.emit()

        except serial.SerialException as e:
            self.port_error.emit(f"Error opening port: {e}")

    def close_port(self):
        if self.thread and self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()
        
        if self.serial and self.serial.is_open:
            self.serial.close()
        
        self.serial = None
        self.thread = None
        self.worker = None
        self.port_closed.emit()

    def send_data(self, data):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write((data + '\r').encode('utf-8'))
            except serial.SerialException as e:
                self.port_error.emit(f"Error sending data: {e}")
        else:
            self.port_error.emit("Port is not open.")
