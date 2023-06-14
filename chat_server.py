#telnet localhost 8888
#python3 chat_server.py
#python3 chat_app.py
import socket
import threading

def receive_message(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(message)
        except:
            break

def main():
    # 建立socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 綁定IP和埠號
    server_socket.bind(('localhost', 8888))

    # 開始監聽
    server_socket.listen()

    print('Server started. Waiting for connections...')

    while True:
        # 接受客戶端連接
        client_socket, client_address = server_socket.accept()
        print(f'Connected with {client_address}')

        # 開啟一個線程接收客戶端訊息
        receive_thread = threading.Thread(target=receive_message, args=(client_socket,))
        receive_thread.start()

        # 主線程用於發送訊息
        while True:
            message = input()
            client_socket.send(message.encode('utf-8'))

    server_socket.close()

if __name__ == '__main__':
    main()
