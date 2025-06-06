import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTextEdit, QDesktopWidget, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

class PortCheckThread(QThread):
    # Signal to send log message back to the UI
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, ip_address, port_prefix, port_range, context_path):
        super().__init__()
        self.ip_address = ip_address
        self.port_prefix = port_prefix
        self.port_range = port_range
        self.context_path = context_path

    def run(self):
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        port_start, port_end = self.port_range
        for i in range(port_start, port_end + 1):
            port = str(i)
            full_port = f"{self.port_prefix}"
            if len(port) == 2:
                full_port = f"{full_port}{port}"
            else:
                full_port = f"{full_port}0{port}"
            
            url = f"{self.ip_address}:{full_port}{self.context_path}"

            try:
                # Execute curl command without redirection and capture output
                result = subprocess.run(
                    ["curl", "-s", url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo
                )

                # Check if the output contains the status "UP"
                if "UP" in result.stdout:
                    self.log_signal.emit(f"{full_port}: UP")
                else:
                    self.log_signal.emit(f"{full_port}: DOWN (Response: {result.stdout.strip()})")

            except Exception as e:
                self.log_signal.emit(f"{full_port}: DOWN (Exception: {e})")

        self.finished_signal.emit()  # Emit finished signal when done


class PortStatusChecker(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('D:\\.env\\app.ico'))

        # Create labels and input boxes with default values
        self.ip_label = QLabel("IP Address")
        self.ip_input = QLineEdit("http://10.2.6.74")  # Default IP Address

        self.port_prefix_label = QLabel("Port prefix")
        self.port_prefix_input = QLineEdit("81")  # Default Port Prefix

        self.port_range_label = QLabel("Port range (e.g., 3,7)")
        self.port_range_input = QLineEdit("3,7")  # Default Port Range

        self.context_path_label = QLabel("Context path")
        self.context_path_input = QLineEdit("/api/actuator/health")  # Default Context Path
        self.context_path_input.setReadOnly(True)

        # Create buttons
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.check_ports)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_console)

        # TextEdit to display console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)  # Make console output read-only

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_input)
        layout.addWidget(self.port_prefix_label)
        layout.addWidget(self.port_prefix_input)
        layout.addWidget(self.port_range_label)
        layout.addWidget(self.port_range_input)
        layout.addWidget(self.context_path_label)
        layout.addWidget(self.context_path_input)

        # Add buttons to a horizontal layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)
        layout.addWidget(self.console_output)

        self.setLayout(layout)
        self.setWindowTitle("ECOMA: Port Status Checker")
        self.setFixedWidth(500)  # Set default width to 500px
        self.center_on_screen()

    def center_on_screen(self):
        """Centers the window on the screen."""
        screen_geometry = QDesktopWidget().availableGeometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry)
        self.move(frame_geometry.topLeft())

    def log_to_console(self, message):
        """Log a message to the console output on the UI."""
        self.console_output.append(message)
        self.console_output.verticalScrollBar().setValue(self.console_output.verticalScrollBar().maximum())

    def clear_console(self):
        """Clear the console output."""
        self.console_output.clear()

    def check_ports(self):
        ip_address = self.ip_input.text()
        port_prefix = self.port_prefix_input.text()
        port_range = self.port_range_input.text().strip("()").split(",")
        context_path = self.context_path_input.text()

        try:
            port_start, port_end = int(port_range[0]), int(port_range[1])
        except (ValueError, IndexError):
            self.log_to_console("Invalid port range. Please enter in format (start,end)")
            return

        # Disable the Run button and change text to "Running..."
        self.run_button.setText("Running...")
        self.run_button.setEnabled(False)

        # Create and start a thread to handle port checking
        self.port_check_thread = PortCheckThread(ip_address, port_prefix, (port_start, port_end), context_path)
        self.port_check_thread.log_signal.connect(self.log_to_console)
        self.port_check_thread.finished_signal.connect(self.on_port_check_finished)
        self.port_check_thread.start()

    def on_port_check_finished(self):
        """Callback when the port check process is finished."""
        self.run_button.setText("Run")
        self.run_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PortStatusChecker()
    window.show()
    sys.exit(app.exec_())
