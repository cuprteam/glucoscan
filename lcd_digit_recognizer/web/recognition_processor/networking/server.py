import socket

from lcd_digit_recognizer.web.recognition_processor.networking.socket_client import SocketClient


class Server(object):
    def __init__(self, listening_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', listening_port))
        s.listen()

        self._listening_socket = s

    def accept_next_client(self):
        conn, addr = self._listening_socket.accept()
        return SocketClient(conn)

