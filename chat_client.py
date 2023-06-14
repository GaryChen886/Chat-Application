import sys
import socket
import os
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog, QInputDialog, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QColor
from PyQt5 import QtCore, QtGui, QtWidgets #works for pyqt5

class Communicate(QObject):
    message_received = pyqtSignal(str)


class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Client")
        self.setGeometry(200, 200, 400, 400)

        self.text_display = QTextEdit(self)
        self.text_display.setReadOnly(True)

        self.text_input = QTextEdit(self)
        self.button_send = QPushButton("Send", self)
        self.button_send.clicked.connect(self.send_message_dialog)

        self.button_send_file = QPushButton("Send File", self)
        self.button_send_file.clicked.connect(self.send_file_dialog)

        layout = QVBoxLayout()
        layout.addWidget(self.text_display)

        input_widget = QWidget()
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.text_input)
        input_layout.addWidget(self.button_send)
        input_widget.setLayout(input_layout)

        layout.addWidget(input_widget)
        layout.addWidget(self.button_send_file)

        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.communicate = Communicate()
        self.communicate.message_received.connect(self.display_message)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('localhost', 8888))

        self.receive_thread = ReceiveThread(self.client_socket, self.communicate.message_received)
        self.receive_thread.start()

    
    
    
    def display_message(self, message, is_sent=False):
        text_color = QColor("blue") if is_sent else QColor("black")
        self.text_display.moveCursor(QtGui.QTextCursor.End)
        self.text_display.setTextColor(text_color)
        self.text_display.insertPlainText(message + "\n")
        

    def send_message_dialog(self):
        message = self.text_input.toPlainText()
        if message:
            self.text_input.clear()
            self.send_message(message)

    def send_message(self, message):
        try:
            message_str = str(message)
            self.client_socket.sendall(message_str.encode('utf-8'))
            self.display_message(f"You: {message_str}", is_sent=True)
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    def send_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName()
        if file_path:
            self.send_file(file_path)

    def send_file(self, file_path):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # Send file command and file name
        self.client_socket.sendall(f"FILE:{file_name}".encode('utf-8'))

        # Send file size
        self.client_socket.sendall(f"SIZE:{file_size}".encode('utf-8'))

        # Send file content
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                self.client_socket.sendall(data)

        self.display_message(f"File sent: {file_name}", is_sent=True)


class ReceiveThread(QObject, threading.Thread):
    def __init__(self, client_socket, signal):
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.signal = signal

    def run(self):
        while True:
            data = self.client_socket.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            self.signal.emit(f"{message}")

            # Check if file command received
            if message.startswith("FILE:"):
                file_name = message[5:]
                self.receive_file(file_name)

        self.client_socket.close()

    def receive_file(self, file_name):
        # Receive file size
        size_data = self.client_socket.recv(1024).decode('utf-8')
        file_size = int(size_data[5:])

        # Receive file content
        received_size = 0
        with open(file_name, 'wb') as file:
            while received_size < file_size:
                data = self.client_socket.recv(1024)
                file.write(data)
                received_size += len(data)

        self.signal.emit(f"File received: {file_name}")


class ChatClient:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = ClientWindow()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    chat_client = ChatClient()
    chat_client.run()
