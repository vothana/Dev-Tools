import sys
import base64
#pip install python-magic-bin
import magic
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTextEdit, QMessageBox, QFileDialog, QHBoxLayout, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class FileProcessingThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, source_in, source_out):
        super().__init__()
        self.source_in = source_in
        self.source_out = source_out

    def run(self):
        try:
            self.log_signal.emit(f"Starting processing: {self.source_in}")
            # Read the base64 string from the file
            with open(self.source_in, "r") as file:
                base64_string = file.read()

            # Decode the base64 string
            file_data = base64.b64decode(base64_string)

            # Detect the file type using the magic library
            file_type = magic.from_buffer(file_data, mime=True)
            self.log_signal.emit(f"Detected file type: {file_type}")

            # Map common MIME types to file extensions
            mime_to_extension = {
                "application/zip": "zip",
                "image/jpeg": "jpg",
                "image/png": "png",
                "application/pdf": "pdf",
                "application/x-7z-compressed": "7z",
            }

            # Get the file extension based on the detected MIME type
            file_extension = mime_to_extension.get(file_type, "bin")  # Default to 'bin' if unknown

            # Create output file path based on the input file name
            output_file_path = f"{self.source_out}.{file_extension}"
            with open(output_file_path, "wb") as output_file:
                output_file.write(file_data)

            self.log_signal.emit(f"File successfully created: {output_file_path}")
            self.finished_signal.emit(output_file_path)
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit("")


class LogOutput(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self.clear)
        context_menu.addAction(clear_action)

        context_menu.exec_(event.globalPos())


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Base64 File Decoder")
        self.setGeometry(100, 100, 700, 500)  # Adjusted height for layout

        # Center the window
        self.center()

        # Create layout
        layout = QVBoxLayout()

        # Input fields with Browse buttons
        layout.addLayout(self.create_input_with_browse("Source Input File Path:", True))
        layout.addLayout(self.create_input_with_browse("Source Output File Path:", False))

        # Log output
        self.log_output = LogOutput()
        self.log_output.setFixedHeight(250)  # Set console message height
        layout.addWidget(self.log_output)

        # Process button
        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self.process_file)
        layout.addWidget(self.process_button)

        # Set the layout to the window
        self.setLayout(layout)

    def create_input_with_browse(self, label_text, is_input):
        """Creates a vertical layout with a label, input field, and a Browse button."""
        layout = QVBoxLayout()

        label = QLabel(label_text)
        input_layout = QHBoxLayout()
        input_field = QLineEdit()

        browse_button = QPushButton("Browse")
        if is_input:
            browse_button.clicked.connect(lambda: self.browse_file(input_field))
            self.source_in = input_field
        else:
            browse_button.clicked.connect(lambda: self.browse_folder(input_field))
            self.source_out = input_field

        input_layout.addWidget(input_field)
        input_layout.addWidget(browse_button)

        layout.addWidget(label)
        layout.addLayout(input_layout)

        return layout

    def browse_file(self, input_field):
        """Opens a file dialog to select a file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            input_field.setText(file_path)

    def browse_folder(self, input_field):
        """Opens a folder dialog to select a folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            input_field.setText(folder_path)
    
    def process_file(self):
        source_in = self.source_in.text()
        file_name = Path(source_in).stem
        source_out = self.source_out.text() + "/" + file_name

        if not source_in or not source_out:
            QMessageBox.warning(self, "Input Error", "Please provide both input and output file paths.")
            return

        self.log_output.append("Processing started...")
        self.process_button.setEnabled(False)

        # Start the background thread
        self.thread = FileProcessingThread(source_in, source_out)
        self.thread.log_signal.connect(self.update_log)
        self.thread.finished_signal.connect(self.processing_finished)
        self.thread.start()

    def update_log(self, message):
        self.log_output.append(message)

    def processing_finished(self, output_file_path):
        self.log_output.append(f"Processing finished.")
        if output_file_path:
            self.log_output.append(f"Output file saved at: {output_file_path}")
        self.process_button.setEnabled(True)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.desktop().screenGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
