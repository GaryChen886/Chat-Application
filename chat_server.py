import sys
import socket
import threading
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor, QColor
from PyQt5.QtGui import QFont, QFontDatabase

class Communicate(QObject):
    message_received = pyqtSignal(str)


class ServerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Server")
        self.setGeometry(200, 200, 400, 400)
        font = QFont("Bradley Hand ITC", 26) 
        self.setFont(font)
        
        self.text_display = QTextEdit(self)
        self.text_display.setReadOnly(True)
        self.setCentralWidget(self.text_display)
        self.text_display.setStyleSheet("background-color: #F0F0F0;")
        font = QFont("Bahnschrift SemiBold", 24, QFont.Bold)
        self.text_display.setFont(font)
        self.text_input = QTextEdit(self)
        self.button_send = QPushButton("Send", self)
        self.button_send.clicked.connect(self.send_message)
        self.button_send.setStyleSheet("background-color: #4CAF50; color: white;")

        self.button_send_file = QPushButton("Send File", self)
        self.button_send_file.clicked.connect(self.send_file_dialog)
        self.button_send_file.setStyleSheet("background-color: #2196F3; color: white;")

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

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 8888))
        self.server_socket.listen(5)

        self.accept_thread = AcceptThread(self.server_socket, self.communicate.message_received)
        self.accept_thread.start()

    def display_message(self, message):
        message_text = message.split(":")[1]  # Separate message content
        message_type = message.split(":")[0]  # Separate message type

        if message_type == "MESSAGE":
            self.append_message(f"You: {message_text}", "blue")
        elif message_type == "FILE":
            file_name = message_text.split("/")[-1]  # Separate file name
            self.append_message(f"File received: {file_name}", "green")
        else:
            self.append_message(message_text, "black")

    def send_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName()
        if file_path:
            self.send_file(file_path)

    def send_file(self, file_path):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # Send file command and file name
        self.broadcast(f"FILE:{file_name}")

        # Send file size
        self.broadcast(f"SIZE:{file_size}")

        # Send file content
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                self.broadcast_data(data)

        self.append_message(f"File sent: {file_name}", "blue")

    def send_message(self):
        message = self.text_input.toPlainText()
        if message:
            self.text_input.clear()
            self.append_message(f"You: {message}", "blue")
            self.broadcast(message)

    def append_message(self, message, color):
        cursor = self.text_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(f'<span style="color: {color};">{message}</span><br>')
        self.text_display.setTextCursor(cursor)
        self.text_display.ensureCursorVisible()

    def broadcast(self, message):
        for client in self.accept_thread.clients:
            try:
                client.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message: {str(e)}")

    def broadcast_data(self, data):
        for client_socket in self.accept_thread.clients:
            try:
                client_socket.sendall(data)
            except Exception as e:
                print(f"Error sending data: {str(e)}")


class AcceptThread(QObject, threading.Thread):
    def __init__(self, server_socket, signal):
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.server_socket = server_socket
        self.signal = signal
        self.clients = []

    def run(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            self.signal.emit(f"Connected with {addr[0]}:{addr[1]}")
            client_thread = ClientThread(client_socket, self.signal, self.broadcast_data)
            self.clients.append(client_socket)
            client_thread.start()

    def broadcast_data(self, data):
        for client_socket in self.clients:
            try:
                client_socket.sendall(data)
            except Exception as e:
                print(f"Error sending data: {str(e)}")


class ClientThread(QObject, threading.Thread):
    def __init__(self, client_socket, signal, broadcast_func):
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.signal = signal
        self.broadcast = broadcast_func

    def run(self):
        while True:
            data = self.client_socket.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            self.signal.emit(f"Message received: {message}")
            self.broadcast(message)

            if message.startswith("FILE:"):
                file_name = message[5:]
                self.receive_file(file_name)

        self.client_socket.close()

    def receive_file(self, file_name):
        size_data = self.client_socket.recv(1024).decode('utf-8')
        file_size = int(size_data[5:])

        received_size = 0
        with open(file_name, 'wb') as file:
            while received_size < file_size:
                data = self.client_socket.recv(1024)
                file.write(data)
                received_size += len(data)

        self.signal.emit(f"File received: {file_name}")


class ChatServer:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = ServerWindow()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    chat_server = ChatServer()
    chat_server.run()
