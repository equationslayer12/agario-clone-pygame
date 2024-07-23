import socket, protocol


class Client:
    """Socket client"""
    def __init__(self, server_host: str) -> None:
        """Initializer"""
        self.socket = socket.socket()
        self.socket.connect((server_host, protocol.PORT))
        print('connected')

    def send_request(self, request: str) -> None:
        """sends from str to bytes to server"""
        self.socket.send(request.encode())

    def get_response(self, num_of_bytes: int = 1024) -> str:
        """receives bytes from server"""
        content = self.socket.recv(num_of_bytes).decode()
        return content

    def close(self) -> None:
        """closes the client socket"""
        self.socket.close()
