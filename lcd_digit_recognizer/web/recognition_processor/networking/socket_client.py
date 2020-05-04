import json
import socket
import traceback


class SocketClient(object):
    encoding = "utf-8"

    def __init__(self, socket=None):
        self._socket = socket
        self._is_connected = True

    @property
    def is_connected(self):
        return self._is_connected

    def connect(self, host, port):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((host, port))
        except Exception:
            self._is_connected = False

    def disconnect(self):
        self._socket.shutdown(socket.SHUT_RDWR)

    def send_json(self, data):
        json_data = json.dumps(data)
        self.send_message(json_data)

    def send_message(self, message: str):
        raw_data_bytes = message.encode(SocketClient.encoding)
        raw_data_bytes_len = len(raw_data_bytes)
        raw_data_bytes_len_bytes = int.to_bytes(raw_data_bytes_len, byteorder="big", length=4)
        if len(raw_data_bytes_len_bytes) != 4:
            AssertionError("Hotspot protocol expects 4 byte length specification")

        try:
            self._atomic_send(raw_data_bytes_len_bytes)
            self._atomic_send(raw_data_bytes)

        except BrokenPipeError:
            # expected behaviour - end silently
            self._is_connected = False
        except Exception:
            self._is_connected = False
            traceback.print_exc()

    def _atomic_send(self, data_bytes):
        data_len = len(data_bytes)
        data_sent_so_far = 0
        while data_sent_so_far < data_len:
            data_sent_so_far += self._socket.send(data_bytes[data_sent_so_far:])

    def read_next_string(self):
        try:
            length_bytes = self._atomic_recv(4)
            length = int.from_bytes(length_bytes, byteorder="big")
            byte_buffer = self._atomic_recv(length)
            raw_data = bytearray(byte_buffer).decode(SocketClient.encoding)

            return raw_data

        except (ConnectionResetError, BrokenPipeError):
            self._is_connected = False
            return None

        except Exception:
            self._is_connected = False
            traceback.print_exc()
            return None

    def _atomic_recv(self, length):
        byte_buffer = []
        missing_bytes = length
        while missing_bytes > 0:
            data = self._socket.recv(missing_bytes)
            received_len = len(data)

            if received_len == 0:
                raise BrokenPipeError("Socket is not connected.")

            missing_bytes -= received_len
            byte_buffer.extend(data)
        return byte_buffer

    def read_next_json(self):
        json_data = self.read_next_string()
        if json_data is None or json_data == "":
            return None
        return json.loads(json_data)
