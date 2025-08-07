import numpy as np
from PySide6.QtCore import QObject, Signal

class DataProcessor(QObject):
    """Parses incoming serial data and manages data buffers."""
    # Signal(index, value)
    pi_data_updated = Signal(int, str)
    # Signal() indicating the buffer has been updated and graph should be redrawn
    mem_data_updated = Signal()
    bk_data_updated = Signal()
    # Signal for unrecognized data for logging
    unrecognized_data = Signal(str)

    def __init__(self, mem_size=5000, bk_size=5000):
        super().__init__()
        # Initialize data buffers similar to Mem_buf and BK_buf in VB code
        self.mem_buf = np.zeros(mem_size, dtype=float)
        self.bk_buf = np.zeros(bk_size, dtype=float)
        # Buffers to store original data for gain/offset adjustments
        self.mem_buf_original = np.zeros(mem_size, dtype=float)
        self.bk_buf_original = np.zeros(bk_size, dtype=float)

    def process_line(self, line: str):
        """Process a single line of data received from the serial port."""
        try:
            line = line.strip()
            if not line:
                return

            header = line[:2]
            parts = line.split(',')

            if header == "PI" and len(parts) >= 3:
                # Format: "PI,##,FFFFFFFFF"
                index = int(parts[1])
                value = parts[2]
                self.pi_data_updated.emit(index, value)

            elif header == "MB" and len(parts) >= 3:
                # Format: "MB,####,FFFF"
                address = int(parts[1])
                if address > 4999: # End of data transmission
                    self.mem_data_updated.emit()
                else:
                    value = float(parts[2])
                    self.mem_buf[address] = value
                    self.mem_buf_original[address] = value

            elif header == "BK" and len(parts) >= 3:
                # Format: "BK,####,FFFF"
                address = int(parts[1])
                if address > 4999: # End of data transmission
                    self.bk_data_updated.emit()
                else:
                    value = float(parts[2])
                    self.bk_buf[address] = value
                    self.bk_buf_original[address] = value
            else:
                # Not a special command, just log it
                self.unrecognized_data.emit(line)

        except (ValueError, IndexError) as e:
            self.unrecognized_data.emit(f"[Parsing Error] {line} - {e}")
