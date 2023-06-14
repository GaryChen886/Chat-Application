import sys
import socket
import threading
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSignal, QObject


class Communicate(QObject):
    message_received = pyqtSignal(str)


class ServerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Server")
        self.setGeometry(200, 200, 400, 400)

        self.text_display = QTextEdit(self)
        self.text_display.setReadOnly(True)
        self.setCentralWidget(self.text_display)
        
        self.button_send_file = QPushButton("Send File", self)
        layout = QVBoxLayout()
        self.button_send_file.clicked.connect(self.send_file_dialog)

        #
        self.text_input = QTextEdit(self)
        self.button_send = QPushButton("Send", self)
        self.button_send.clicked.connect(self.send_message)

        
        

        layout = QVBoxLayout()
        layout.addWidget(self.text_display)
        layout.addWidget(self.button_send_file)

        # main_widget = QWidget(self)
        # main_widget.setLayout(layout)
        main_widget = QWidget(self)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.setCentralWidget(main_widget)
        layout.addWidget(self.text_input)
        layout.addWidget(self.button_send)
        self.communicate = Communicate()
        self.communicate.message_received.connect(self.display_message)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 8888))
        self.server_socket.listen(5)

        self.accept_thread = AcceptThread(self.server_socket, self.communicate.message_received)
        self.accept_thread.start()

    def display_message(self, message):
        self.text_display.append(message)

    def send_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName()
        if file_path:
            self.send_file(file_path)

    def send_file(self, file_path):
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # 發送檔案指令和檔案名稱
        self.broadcast(f"FILE:{file_name}")

        # 發送檔案大小
        self.broadcast(f"SIZE:{file_size}")

        # 發送檔案內容
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                self.broadcast_data(data)

        self.text_display.append(f"File sent: {file_name}")
        
    def send_message(self):
        message = self.text_input.toPlainText()
        if message:
            self.text_input.clear()
            self.broadcast(f"MESSAGE:{message}")

    
    def broadcast(self, message):
        for client in self.accept_thread.clients:
            try:
                client.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message: {str(e)}")

    # def broadcast_data(self, data):
    #     for client in self.accept_thread.clients:
    #         try:
    #             client.sendall(data)
    #         except Exception as e:
    #             print(f"Error sending data: {str(e)}")
    def broadcast_data(self, data):
        for client_socket in self.clients:
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

    # def broadcast_data(self, data):
    #     for client in self.clients:
    #         try:
    #             client.sendall(data)
    #         except Exception as e:
    #             print(f"Error sending data: {str(e)}")
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

            # 檢查是否收到檔案指令
            if message.startswith("FILE:"):
                file_name = message[5:]
                self.receive_file(file_name)

        self.client_socket.close()

    def receive_file(self, file_name):
        # 接收檔案大小
        size_data = self.client_socket.recv(1024).decode('utf-8')
        file_size = int(size_data[5:])

        # 接收檔案內容
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
