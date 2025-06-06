from PyQt5.QtWidgets import QMainWindow, QTabWidget, QApplication, QDesktopWidget
from FrontendRunnerApp import FrontendRunnerTab
from PortKiller import PortKillerTab
import sys
import os
import ctypes
from PyQt5.QtGui import QIcon

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dev Tools")
        self.setGeometry(100, 100, 900, 700)
        
        # Set Windows taskbar icon
        if sys.platform == 'win32':
            myappid = 'com.yourcompany.frontendrunner.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        self.setWindowIcon(QIcon(self.get_resource_path('PROFILE_PIC.ico')))
        self.center_window()
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Add frontend runner tab
        self.frontend_tab = FrontendRunnerTab()
        self.tabs.addTab(self.frontend_tab, "Frontend Runner")
        
        # Add port killer tab
        self.port_killer_tab = PortKillerTab()
        self.tabs.addTab(self.port_killer_tab, "Port Killer")
        
        # Set central widget
        self.setCentralWidget(self.tabs)

    def center_window(self):
        """Center the window on the screen"""
        frame = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def get_resource_path(self, relative_path):
        """Get absolute path to resource"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('PROFILE_PIC.ico'))
    window = MainApp()
    window.show()
    sys.exit(app.exec_())