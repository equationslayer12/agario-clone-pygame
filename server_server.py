import socket


class Server:
    """Socket server"""
    def __init__(self, host, port):
        """Initializer"""
        self.host = host
        self.port = port
        self.socket = self.init_server()
        self.clients = []

    def init_server(self):
        """Initialize server socket and start listening"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        return server_socket

    def connect_client(self):
        """Wait for a client to connect"""
        client_socket, client_address = self.socket.accept()
        return client_socket, client_address

    def close(self):
        """Close server socket"""
        self.socket.close()

    def receive(self, client_socket, receive_in_bytes=False, num_of_bytes=1024):
        """Wait for client to send data"""
        if receive_in_bytes:
            return client_socket.recv(num_of_bytes)
        else:
            return client_socket.recv(num_of_bytes).decode()

    def send(self, client_socket, data):
        """Send data to client"""
        client_socket.send(data.encode())
