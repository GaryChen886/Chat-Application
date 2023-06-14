import sys
import socket
import os
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog, QInputDialog
from PyQt5.QtCore import pyqtSignal, QObject


class Communicate(QObject):
    message_received = pyqtSignal(str)


class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Client")
        self.setGeometry(200, 200, 400, 400)

        self.text_display = QTextEdit(self)
        self.text_display.setReadOnly(True)
        self.setCentralWidget(self.text_display)

        self.button_send_message = QPushButton("Send Message", self)
        self.button_send_message.clicked.connect(self.send_message_dialog)

        self.button_send_file = QPushButton("Send File", self)
        self.button_send_file.clicked.connect(self.send_file_dialog)

        layout = QVBoxLayout()
        layout.addWidget(self.text_display)
        layout.addWidget(self.button_send_message)
        layout.addWidget(self.button_send_file)

        main_widget = QWidget(self)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.communicate = Communicate()
        self.communicate.message_received.connect(self.display_message)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('localhost', 8888))

        self.receive_thread = ReceiveThread(self.client_socket, self.communicate.message_received)
        self.receive_thread.start()

    def display_message(self, message):
        self.text_display.append(message)

    def send_message_dialog(self):
        message, ok = QInputDialog.getText(self, "Send Message", "Enter message:")
        if ok:
            self.send_message(message)

    def send_message(self, message):
        try:
            self.client_socket.sendall(message.encode('utf-8'))
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

        self.text_display.append(f"File sent: {file_name}")


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
            self.signal.emit(f"Message received: {message}")

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
