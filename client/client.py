import queue
import socket
import threading
import time
import logging
import sys

import buffer

debug: bool = False
MAX_LENGTH: int = -1

_current_time = 0


def ticker(time_break: float) -> bool:
    global _current_time

    if _current_time == 0:
        _current_time = time.time()
        return False
    else:
        current_time_break = time.time() - _current_time
        if current_time_break >= time_break:
            _current_time = time.time()
            return True
        else:
            return False


#  log config
file_log = True

_format_msg = "[%(levelname)s] [%(asctime)s] [%(funcName)s] %(message)s"
_format_time = "%H:%M:%S"

_formatter = logging.Formatter(_format_msg, _format_time)

_file_handler = logging.FileHandler("ServerLog.log", mode='a', encoding='utf-8')
_file_handler.setFormatter(_formatter)
_file_handler.setLevel(logging.DEBUG)

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_formatter)
_console_handler.setLevel(logging.DEBUG)

_log = logging.getLogger("ClientLog")
if debug:
    _log.setLevel(logging.DEBUG)
else:
    _log.setLevel(logging.INFO)
_log.addHandler(_console_handler)
if file_log:
    _log.addHandler(_file_handler)

    with open("ServerLog.log", mode='a', encoding='utf_8') as log_file:
        log_file.write("===================================LOG START===================================\n")


class Client(object):
    """the part which connected with a server, provide two queues to pass data"""
    _data_queue_1 = queue.Queue()  # for data from java to server
    _data_queue_2 = queue.Queue()  # for data from server to java

    def __init__(self, server_addr: tuple[str, int]):
        self.server_addr = server_addr

        self._encoding = 'utf_8'
        self._server: socket.socket

        self._buf = buffer.Buffer()
        self._event = threading.Event()

        self.__create_socket()

    def __create_socket(self):
        """connect to server"""
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.connect(self.server_addr)

        data = self._server.recv(MAX_LENGTH)
        print(data.decode(self._encoding))

    def get_data(self):
        """get data from server"""
        while True:
            data = self._server.recv(MAX_LENGTH)

            if data == b"SIGNAL":  # the other recv data successfully
                self._event.set()

            elif data[0:3] == b"LEN":
                self._buf.set_length(int.from_bytes(data[3:]))
                _log.debug(int.from_bytes(data[3:]))
                self._server.send(b"SIGNAL")  # show the other that we recv data successfully

            else:
                self._buf.put(data)

                complete = self._buf.get()
                _log.debug(f"complete: {complete}, {self._buf.total_size}, {self._buf.length}")

                if complete:
                    self._data_queue_2.put(complete)
                    _log.debug(data)

    def send_data(self):
        """send data to server"""
        while True:
            data = self._data_queue_1.get()
            if data:
                self._server.send(b''.join([b'LEN', len(data).to_bytes(8)]))
                self._event.wait()
                self._server.sendall(data)
                self._event.clear()

                _log.debug(data)
