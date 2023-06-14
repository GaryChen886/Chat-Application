import sys
import socket
import threading
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton


class Communicate(QObject):
    message_received = pyqtSignal(str)
    send_message = pyqtSignal(str)


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

        self.communicate = Communicate()

        self.send_button.clicked.connect(self.send_message)

        self.communicate.message_received.connect(self.display_message)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('localhost', 8888))
        self.receive_thread = ReceiveThread(self.client_socket, self.communicate.message_received)
        self.receive_thread.start()

    def send_message(self):
        message = self.message_input.text()
        self.communicate.send_message.emit(message)
        self.message_input.clear()
        self.client_socket.send(message.encode('utf-8'))

    def display_message(self, message):
        self.message_display.append(message)


class ReceiveThread(QObject, threading.Thread):
    def __init__(self, client_socket, signal):
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.signal = signal

    def run(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                self.signal.emit(message)
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
