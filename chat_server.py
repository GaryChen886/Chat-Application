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
    # socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind IP
    server_socket.bind(('localhost', 8888))

    # Listen
    server_socket.listen()

    print('Server started. Waiting for connections...')

    while True:
        # Accept connection
        client_socket, client_address = server_socket.accept()
        print(f'Connected with {client_address}')

        # Thread for receiving message
        receive_thread = threading.Thread(target=receive_message, args=(client_socket,))
        receive_thread.start()

        # Send message
        while True:
            message = input()
            client_socket.send(message.encode('utf-8'))

    server_socket.close()

if __name__ == '__main__':
    main()
