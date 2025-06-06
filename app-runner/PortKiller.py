from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTextEdit, QMessageBox)
from PyQt5.QtCore import QProcess
import subprocess
import sys

class PortKillerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Port input section
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("e.g., 3000")
        port_layout.addWidget(self.port_input)
        
        # Kill button
        self.kill_btn = QPushButton("Kill Port")
        self.kill_btn.clicked.connect(self.kill_port)
        self.kill_btn.setToolTip("Force kill all processes using this port")
        
        # Console output
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: black;
                color: white;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)
        
        # Add widgets to layout
        layout.addLayout(port_layout)
        layout.addWidget(self.kill_btn)
        layout.addWidget(self.console)
        
    def kill_port(self):
        port = self.port_input.text().strip()
        if not port.isdigit():
            self.show_error("Please enter a valid port number")
            return
            
        if sys.platform != 'win32':
            self.show_error("Port killer currently only supports Windows")
            return
            
        try:
            self.console.append(f"Searching for processes using port {port}...")
            
            # Find processes using the port
            netstat_cmd = f'netstat -ano | findstr ":{port}"'
            result = subprocess.run(
                netstat_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                self.console.append(f"No processes found using port {port}")
                return
                
            self.console.append("Found processes:\n" + result.stdout)
            
            # Kill all found processes
            kill_cmd = f'for /f "tokens=5" %p in (\'netstat -a -n -o ^| findstr ":{port}"\') do taskkill /PID %p /F'
            subprocess.run(kill_cmd, shell=True)
            
            self.console.append(f"\nAttempted to kill all processes using port {port}")
            self.console.append("Operation completed")
            
        except subprocess.CalledProcessError as e:
            self.show_error(f"Command failed: {e.stderr}")
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
            
    def show_error(self, message):
        """Show error message in console and as dialog"""
        self.console.append(f"Error: {message}")
        QMessageBox.warning(self, "Error", message)