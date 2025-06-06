import os
import sys
import json
import ctypes
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QLabel, QComboBox, QPushButton, QTextEdit, QLineEdit, 
                             QFileDialog, QCheckBox, QMessageBox, QCompleter)
from PyQt5.QtCore import QProcess, QTextStream, Qt, QSettings, QProcessEnvironment, QStringListModel
from PyQt5.QtGui import QTextCursor, QFont, QTextCharFormat, QColor, QTextCursor, QIcon



class FrontendRunnerApp(QMainWindow):
    def __init__(self):
        super().__init__()
               # Add this initialization
        self.current_format = QTextCharFormat()
        self.current_format.setForeground(QColor('white'))
        # Set Windows taskbar icon
        if sys.platform == 'win32':
            myappid = 'com.yourcompany.frontendrunner.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.setWindowIcon(QIcon(self.get_resource_path('PROFILE_PIC.ico')))
        self.setWindowTitle("Frontend Project Runner")
        self.resize(900, 700)
        self.center_window()
        self.config_json_path = None

        # Initialize settings
        self.settings = QSettings("FrontendRunner", "FrontendRunner")
        self.load_config()
        
        # Initialize process
        self.process = None
        self.console_output = None
        self.running_port = None
        
        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        
        # Status bar for showing running project and port
        self.statusBar().showMessage("Ready")
        
        # UI Elements
        self.create_project_selection()
        self.create_node_selection()
        self.create_command_selection()
        self.create_action_buttons()
        self.create_console_output()
        
        # Initialize data
        self.load_projects()
        self.load_node_versions()
    
    def get_resource_path(self, relative_path):
        """Get absolute path to resource"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
        
    def center_window(self):
        frame = self.frameGeometry()
        center_point = QApplication.desktop().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())
    
    def load_config(self):
        """Load configuration with proper path handling"""
        # Get the directory where the executable or script is running from
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Set config file path
        self.config_json_path = os.path.join(base_dir, "config.json")
        
        # Default configuration
        self.config = {
            "NVM_DIR": "D:\\window\\nvm",
            "DEFAULT_PROJECT_DIR": "D:\\front",
            "RUNNER_COMMANDS": [
                "yarn dev", 
                "npm run dev", 
                "npm run serve", 
                "yarn start", 
                "npm start"
            ],
            "SERVICES": []
        }
        
        try:
            # Create config file if it doesn't exist
            if not os.path.exists(self.config_json_path):
                with open(self.config_json_path, "w") as f:
                    json.dump(self.config, f, indent=4)
                self.append_console(f"Created new config file at {self.config_json_path}")
            else:
                # Load from existing config file
                with open(self.config_json_path, "r") as f:
                    file_config = json.load(f)
                    # Merge with defaults (preserve any existing settings)
                    self.config.update(file_config)
                    
        except Exception as e:
            error_msg = f"Error loading config: {str(e)}"
            self.append_console(error_msg)
            QMessageBox.warning(self, "Config Error", error_msg)
            
            # Try to create fresh config if loading failed
            try:
                with open(self.config_json_path, "w") as f:
                    json.dump(self.config, f, indent=4)
                self.append_console("Created fresh config file due to load error")
            except Exception as e:
                critical_msg = f"Failed to create config file: {str(e)}"
                self.append_console(critical_msg)
                QMessageBox.critical(self, "Config Error", critical_msg)
        
        # Ensure required directories exist
        os.makedirs(self.config["NVM_DIR"], exist_ok=True)
        os.makedirs(self.config["DEFAULT_PROJECT_DIR"], exist_ok=True)
    
    def save_config(self):
        with open(self.config_json_path, "w") as f:
            json.dump(self.config, f, indent=4)

        # Also save to QSettings
        self.settings.setValue("NVM_DIR", self.config["NVM_DIR"])
        self.settings.setValue("DEFAULT_PROJECT_DIR", self.config["DEFAULT_PROJECT_DIR"])
        self.settings.setValue("RUNNER_COMMANDS", json.dumps(self.config["RUNNER_COMMANDS"]))

    
    def create_project_selection(self):
        project_layout = QHBoxLayout()
        
        project_label = QLabel("Project:")
        self.project_combo = QComboBox()
        self.project_combo.setEditable(True)
        
        # Set up auto-completion
        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.project_combo.setCompleter(completer)
        
        # Load projects from config
        self.load_projects_from_config()
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_project)
        
        # Connect signals to auto-update other fields when project changes
        self.project_combo.currentTextChanged.connect(self.update_fields_from_project)
        
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_combo)
        project_layout.addWidget(browse_button)
        
        self.layout.addLayout(project_layout)

    def load_projects_from_config(self):
        """Load projects from config.json SERVICES section"""
        try:
            with open(self.config_json_path, 'r') as f:
                config = json.load(f)
                services = config.get('SERVICES', [])
                
                self.project_combo.clear()
                self.projects_config = {}  # Store project configs for reference
                
                for service in services:
                    name = service.get('SERVICE_NAME', '')
                    path = service.get('SERVICE_DIR', '')
                    if name and path:
                        self.project_combo.addItem(f"{name}={path}")
                        self.projects_config[f"{name} ({path})"] = service
                
                # Update completer model
                model = QStringListModel([self.project_combo.itemText(i) for i in range(self.project_combo.count())])
                self.project_combo.completer().setModel(model)
                
        except Exception as e:
            print(f"Error loading projects from config: {str(e)}")

    def update_fields_from_project(self, project_text):
        """Update other fields when project is selected"""
        if not hasattr(self, 'projects_config') or project_text not in self.projects_config:
            return
        
        config = self.projects_config[project_text]
        
        # Update Node version
        node_version = f"v{config.get('NODE_VERSION', '')}"
        index = self.node_combo.findText(node_version)
        if index >= 0:
            self.node_combo.setCurrentIndex(index)
        
        # Update run command
        run_command = config.get('RUN_COMMAND', '')
        index = self.command_combo.findText(run_command)
        if index >= 0:
            self.command_combo.setCurrentIndex(index)
        elif run_command:  # Add if not exists
            self.command_combo.addItem(run_command)
            self.command_combo.setCurrentIndex(self.command_combo.count() - 1)
        
        # Update npm install checkbox
        self.install_checkbox.setChecked(config.get('NMP_INSTALL', False))

    def browse_project(self):
        """Browse for project directory and add to config"""
        default_dir = self.config.get("DEFAULT_PROJECT_DIR", "D:\\front")
        folder = QFileDialog.getExistingDirectory(self, "Select Project Directory", default_dir)
        
        if folder:
            # Add to combo if not already present
            project_name = os.path.basename(folder)
            display_text = f"{project_name} ({folder})"
            
            if self.project_combo.findText(display_text) == -1:
                self.project_combo.addItem(display_text)
                # Update completer model
                model = QStringListModel([self.project_combo.itemText(i) for i in range(self.project_combo.count())])
                self.project_combo.completer().setModel(model)
            
            self.project_combo.setCurrentText(display_text)
    
    def create_node_selection(self):
        node_layout = QHBoxLayout()
        
        node_label = QLabel("Node Version:")
        self.node_combo = QComboBox()
        
        node_layout.addWidget(node_label)
        node_layout.addWidget(self.node_combo)
        
        self.layout.addLayout(node_layout)
    
    def create_command_selection(self):
        command_layout = QHBoxLayout()
        
        command_label = QLabel("Run Command:")
        self.command_combo = QComboBox()
        self.command_combo.addItems(self.config["RUNNER_COMMANDS"])
        self.command_combo.setEditable(True)
        
        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_combo)
        
        self.layout.addLayout(command_layout)
    
    def create_action_buttons(self):
        button_layout = QHBoxLayout()
        
        self.install_checkbox = QCheckBox("Run npm install before starting")
        self.install_checkbox.setChecked(False)
        
        self.run_button = QPushButton("Run Project")
        self.run_button.clicked.connect(self.run_project)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_project)
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.install_checkbox)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        
        self.layout.addLayout(button_layout)
    
    def create_console_output(self):
        console_label = QLabel("Console Output:")
        self.layout.addWidget(console_label)
        
        self.console_output = QTextEdit()
        self.console_output.setFont(QFont("Courier New", 10))
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: black;
                color: white;
                border: 1px solid #444;
                font-family: Consolas, monospace;
            }
        """)
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter custom command and press Enter...")
        self.command_input.returnPressed.connect(self.execute_custom_command)
        
        self.layout.addWidget(self.console_output)
        self.layout.addWidget(self.command_input)
    
    def browse_project(self):
        default_dir = self.config["DEFAULT_PROJECT_DIR"]
        folder = QFileDialog.getExistingDirectory(self, "Select Project Directory", default_dir)
        if folder:
            self.project_combo.addItem(folder)
            self.project_combo.setCurrentText(folder)
    
    def load_projects(self):
        # Load projects from default directory
        front_dir = self.config["DEFAULT_PROJECT_DIR"]
        if os.path.exists(front_dir):
            for item in os.listdir(front_dir):
                full_path = os.path.join(front_dir, item)
                if os.path.isdir(full_path):
                    self.project_combo.addItem(full_path)
    
    def load_node_versions(self):
        # Load node versions from nvm directory
        nvm_dir = self.config["NVM_DIR"]
        if os.path.exists(nvm_dir):
            for item in os.listdir(nvm_dir):
                if item.startswith("v") and os.path.isdir(os.path.join(nvm_dir, item)):
                    self.node_combo.addItem(item)
    
    def set_node_version(self, version):
        # Set the PATH environment to use the selected Node version
        nvm_dir = self.config["NVM_DIR"]
        node_path = os.path.join(nvm_dir, version)
        
        # Get current PATH and remove any existing Node paths
        current_path = os.environ.get("PATH", "").split(";")
        filtered_path = [p for p in current_path if not p.startswith(nvm_dir)]
        
        # Add the selected Node version to PATH
        new_path = [node_path, nvm_dir] + filtered_path
        os.environ["PATH"] = ";".join(new_path)
        
        self.append_console(f"Node version set to: {version}")
    
    def append_console(self, text):
        self.console_output.moveCursor(QTextCursor.End)
        self.console_output.insertPlainText(text + "\n")
        self.console_output.moveCursor(QTextCursor.End)
    
    def run_project(self):
        ccText = self.project_combo.currentText().split("=")[1]
        project_dir = ccText
        print("currentText : ", self.project_combo.currentText())
        print("DIRR : ", project_dir)
        if not project_dir or not os.path.exists(project_dir):
            self.append_console("Error: Invalid project directory")
            return
        
        # Update status bar with running project name
        project_name = os.path.basename(project_dir)
        self.statusBar().showMessage(f"Running: {project_name}")
        
        self.set_node_version(project_dir)
        
        # Run npm install if checkbox is checked
        if self.install_checkbox.isChecked():
            self.run_npm_install(project_dir)
            # We'll chain the actual run after install completes
            return
        
        # Proceed with running the project
        self.execute_run_command(project_dir)
    
    def run_npm_install(self, project_dir):
        self.append_console(f"Running npm install in {project_dir}...")
        
        self.process = QProcess()
        self.process.setWorkingDirectory(project_dir)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(lambda: self.on_install_finished(project_dir))
        
        # Determine package manager (check for yarn.lock)
        if os.path.exists(os.path.join(project_dir, "yarn.lock")):
            self.process.start("yarn", ["install"])
        else:
            self.process.start("npm", ["install"])
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def on_install_finished(self, project_dir):
        self.append_console("npm install completed")
        self.execute_run_command(project_dir)
    
    def execute_run_command(self, project_dir):
        command = self.command_combo.currentText().strip()
        if not command:
            self.append_console("Error: No run command specified")
            return
        
        parts = command.split()
        program = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Set up environment with correct Node version
        nvm_dir = self.config["NVM_DIR"]
        node_version = self.node_combo.currentText()
        node_path = os.path.join(nvm_dir, node_version)
        
        # Get current environment
        env = QProcessEnvironment.systemEnvironment()
        
        # Update PATH - prepend Node version and nvm dir
        current_path = env.value("PATH", "")
        new_path = f"{node_path};{nvm_dir};{current_path}"
        env.insert("PATH", new_path)
        
        # Windows-specific: Set NVM_HOME and NVM_SYMLINK if they exist
        if 'NVM_HOME' in os.environ:
            env.insert("NVM_HOME", os.environ['NVM_HOME'])
        if 'NVM_SYMLINK' in os.environ:
            env.insert("NVM_SYMLINK", os.environ['NVM_SYMLINK'])
        
        # Temporarily update os.environ for executable checking
        old_path = os.environ['PATH']
        os.environ['PATH'] = new_path
        
        # Check if program exists (Windows specific)
        program_path = self.find_executable(program)
        if not program_path:
            self.append_console(f"Error: Cannot find '{program}' in PATH")
            self.append_console(f"Current PATH: {new_path}")
            self.append_console("Please ensure:")
            self.append_console(f"1. Node version {node_version} exists in {nvm_dir}")
            self.append_console(f"2. {program} is installed (try 'nvm install {node_version}')")
            os.environ['PATH'] = old_path
            return
        
        os.environ['PATH'] = old_path
        
        self.append_console(f"Running command: {command} in {project_dir}...")
        self.append_console(f"Using Node: {node_version}")
        self.append_console(f"Using {program}: {program_path}")
        
        self.process = QProcess()
        self.process.setWorkingDirectory(project_dir)
        self.process.setProcessEnvironment(env)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        try:
            # Windows-specific: For yarn/npm, we need to run the .cmd file
            if program in ['yarn', 'npm'] and not program_path.endswith('.cmd'):
                program_path = program_path.replace('.exe', '.cmd')
                if not os.path.exists(program_path):
                    program_path = os.path.join(node_path, f"{program}.cmd")
            
            # Windows-specific: Need to run through cmd.exe for proper environment
            if program_path.endswith('.cmd'):
                args = ['/c', program_path] + args
                program_path = 'cmd.exe'
            
            self.append_console(f"Executing: {program_path} {' '.join(args)}")
            self.process.start(program_path, args)
            
            if not self.process.waitForStarted(1000):
                error = self.process.errorString()
                self.append_console(f"Failed to start process: {error}")
                self.append_console("Troubleshooting steps:")
                self.append_console(f"1. Verify file exists: {program_path}")
                self.append_console(f"2. Check file permissions")
                self.append_console(f"3. Try running manually in cmd: {command}")
                self.process_finished(-1, QProcess.CrashExit)
                return
                
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
        except Exception as e:
            self.append_console(f"Error executing command: {str(e)}")
            self.process_finished(-1, QProcess.CrashExit)

    def find_executable(self, name):
        """Check if an executable exists in the PATH (Windows specific)"""
        # Windows executable extensions to check
        extensions = ['.cmd', '.bat', '.exe', '']
        
        paths = os.environ['PATH'].split(os.pathsep)
        for path in paths:
            for ext in extensions:
                full_path = os.path.join(path, name + ext)
                if os.path.isfile(full_path):
                    return full_path
        return None

    def stop_project(self):
        if self.process and self.process.state() == QProcess.Running:
            self.append_console("Stopping process...")
            
            # First try graceful termination
            self.process.terminate()
            
            # Wait for clean shutdown (5 seconds)
            if not self.process.waitForFinished(5000):
                self.append_console("Process not responding - forcing termination...")
                
                # Windows-specific: Kill the entire process tree
                if sys.platform == 'win32':
                    self.kill_windows_process_tree(self.process.processId())
                else:
                    self.process.kill()
                
                # Double-check and wait
                if not self.process.waitForFinished(1000):
                    self.append_console("Warning: Process might still be running")
            
            self.append_console("Process stopped")
            self.cleanup_after_stop()
        else:
            self.append_console("No running process to stop")
    
    def closeEvent(self, event):
        """Handle application closing"""
        if self.process and self.process.state() == QProcess.Running:
            reply = QMessageBox.question(
                self,
                'Process Running',
                'A service is still running. Do you want to stop it before exiting?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self.kill_windows_process_tree(self.process.processId())
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()  # Continue closing without stopping
            else:
                event.ignore()  # Cancel closing
        else:
            event.accept()

    def kill_windows_process_tree(self, pid):
        """Forcefully kill a process and all its children on Windows"""
        try:
            import psutil
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Kill all children first
            for child in children:
                try:
                    child.kill()
                except:
                    pass
            
            # Then kill parent
            try:
                parent.kill()
            except:
                pass
            
            return True
        except Exception as e:
            self.append_console(f"Error killing process tree: {str(e)}")
            # Fallback to taskkill if psutil fails
            try:
                import subprocess
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(pid)])
                return True
            except Exception as e:
                self.append_console(f"Taskkill also failed: {str(e)}")
                return False

    def cleanup_after_stop(self):
        """Clean up after process stopped"""
        self.statusBar().showMessage("Ready")
        self.running_port = None
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.process = None
    
    def execute_custom_command(self):
        command = self.command_input.text().strip()
        if not command:
            return
        
        project_dir = self.project_combo.currentText()
        if not project_dir or not os.path.exists(project_dir):
            self.append_console("Error: Invalid project directory")
            return
        
        self.append_console(f"Executing custom command: {command}")
        self.command_input.clear()
        
        self.process = QProcess()
        self.process.setWorkingDirectory(project_dir)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        # Split command into parts
        parts = command.split()
        program = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        
        self.process.start(program, args)
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def handle_stdout(self):
        if self.process:
            data = self.process.readAllStandardOutput()
            stream = QTextStream(data)
            text = stream.readAll()
            self.process_console_text(text)
            self.detect_running_port(text)

    def handle_stderr(self):
        if self.process:
            data = self.process.readAllStandardError()
            stream = QTextStream(data)
            text = stream.readAll()
            self.process_console_text(text)
            self.detect_running_port(text)

    def process_console_text(self, text):
        """Process text with ANSI color codes and append to console"""
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Split text into segments with ANSI codes
        segments = self.split_ansi_segments(text)
        
        for segment in segments:
            if segment.startswith('\x1B['):
                # ANSI color code - update format
                self.current_format = self.ansi_to_text_format(segment)
                cursor.setCharFormat(self.current_format)
            else:
                # Normal text - insert with current format
                cursor.insertText(segment)
        
        self.console_output.ensureCursorVisible()

    def split_ansi_segments(self, text):
        """Split text into segments separated by ANSI codes"""
        import re
        return re.split('(\x1B\[[0-?]*[ -/]*[@-~])', text)

    def ansi_to_text_format(self, ansi_code):
        """Convert ANSI code to QTextCharFormat"""
        format = QTextCharFormat()
        
        # Default to white text
        format.setForeground(QColor('white'))
        
        # Remove ESC[ and final m
        codes = ansi_code[2:-1].split(';')
        
        for code in codes:
            if not code:
                continue
                
            code = int(code)
            
            # Basic colors
            if code == 0:    # Reset
                format.setForeground(QColor('white'))
            elif code == 30: # Black
                format.setForeground(QColor('black'))
            elif code == 31: # Red
                format.setForeground(QColor('red'))
            elif code == 32: # Green
                format.setForeground(QColor('green'))
            elif code == 33: # Yellow
                format.setForeground(QColor('yellow'))
            elif code == 34: # Blue
                format.setForeground(QColor('blue'))
            elif code == 35: # Magenta
                format.setForeground(QColor('magenta'))
            elif code == 36: # Cyan
                format.setForeground(QColor('cyan'))
            elif code == 37: # White
                format.setForeground(QColor('white'))
                
            # Bright colors
            elif code == 90: # Bright Black (Gray)
                format.setForeground(QColor('gray'))
            elif code == 91: # Bright Red
                format.setForeground(QColor(255, 100, 100))  # Lighter red
            elif code == 92: # Bright Green
                format.setForeground(QColor(100, 255, 100))  # Lighter green
            elif code == 93: # Bright Yellow
                format.setForeground(QColor(255, 255, 100)) # Lighter yellow
            elif code == 94: # Bright Blue
                format.setForeground(QColor(100, 100, 255)) # Lighter blue
            elif code == 95: # Bright Magenta
                format.setForeground(QColor(255, 100, 255)) # Lighter magenta
            elif code == 96: # Bright Cyan
                format.setForeground(QColor(100, 255, 255)) # Lighter cyan
            elif code == 97: # Bright White
                format.setForeground(QColor('white'))
                
            # Background colors (optional)
            elif 40 <= code <= 47:  # Standard background colors
                pass  # Implement if you want background colors
            elif 100 <= code <= 107: # Bright background colors
                pass  # Implement if you want background colors
                
        return format
    
    def detect_running_port(self, text):
        # Try to find port number in the output
        port_patterns = [
            "on port (\d+)",
            ":\d+",  # Matches :3000, :8080 etc.
            "port (\d+)",
            "http://[^:]+:(\d+)"
        ]
        
        for pattern in port_patterns:
            import re
            match = re.search(pattern, text)
            if match:
                self.running_port = match.group(1) if len(match.groups()) > 0 else match.group(0)
                project_name = os.path.basename(self.project_combo.currentText())
                self.statusBar().showMessage(f"Running: {project_name} (Port: {self.running_port})")
                break
    
    def process_finished(self, exit_code, exit_status):
        self.append_console(f"Process finished with exit code {exit_code}")
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.process = None
        self.statusBar().showMessage("Ready")
        self.running_port = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('PROFILE_PIC.ico'))
    window = FrontendRunnerApp()
    window.show()
    sys.exit(app.exec_())