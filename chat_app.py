import sys
import socket
import threading
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QFileDialog


class Communicate(QObject):
    message_received = pyqtSignal(str)
    send_message = pyqtSignal(str)
    file_selected = pyqtSignal(str)
    file_sent = pyqtSignal(str)
    file_received = pyqtSignal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Application")
        self.setGeometry(200, 200, 400, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.send_button = QPushButton("Send")

        self.layout.addWidget(self.message_display)
        self.layout.addWidget(self.message_input)
        self.layout.addWidget(self.send_button)

        self.file_select_button = QPushButton("Select File")
        self.layout.addWidget(self.file_select_button)

        self.communicate = Communicate()

        self.send_button.clicked.connect(self.send_message)
        self.file_select_button.clicked.connect(self.select_file)

        self.communicate.message_received.connect(self.display_message)
        self.communicate.file_selected.connect(self.send_file)
        self.communicate.file_sent.connect(self.display_file_sent)
        self.communicate.file_received.connect(self.display_file_received)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('localhost', 8888))
        self.receive_thread = ReceiveThread(self.client_socket, self.communicate.message_received,
                                            self.communicate.file_received)
        self.receive_thread.start()

    def send_message(self):
        message = self.message_input.text()
        self.communicate.send_message.emit(message)
        self.message_input.clear()
        self.client_socket.send(message.encode('utf-8'))

    def display_message(self, message):
        self.message_display.append(message)

    def select_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select File")
        self.communicate.file_selected.emit(file_path)

    def send_file(self, file_path):
        with open(file_path, 'rb') as file:
            file_data = file.read()
        self.client_socket.sendall(file_data)
        self.communicate.file_sent.emit(f"File sent: {file_path}")

    def display_file_sent(self, message):
        self.message_display.append(message)

    def display_file_received(self, file_path):
        self.message_display.append(f"File received: {file_path}")


class ReceiveThread(QObject, threading.Thread):
    def __init__(self, client_socket, message_signal, file_signal):
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.message_signal = message_signal
        self.file_signal = file_signal

    def run(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                if data.startswith(b'FILE:'):
                    file_name = data.decode('utf-8')[5:]
                    with open(file_name, 'wb') as file:
                        while True:
                            data = self.client_socket.recv(1024)
                            if not data:
                                break
                            file.write(data)
                    self.file_signal.emit(file_name)
                else:
                    message = data.decode('utf-8')
                    self.message_signal.emit(message)
            except:
                break


class ChatApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    chat_app = ChatApplication()
    chat_app.run()
