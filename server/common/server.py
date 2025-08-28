# FILE: common/server.py

import socket
import logging
import signal
import sys
from .protocol import Protocol
from .bet_handler import BetHandler

class Server:
    def __init__(self, port, listen_backlog):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._active_connections = []
        self._handler = BetHandler()
        self.__setup_signal_handlers()

    def run(self):
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        addr = client_sock.getpeername()
        logging.info(f'action: client_connection | result: success | ip: {addr[0]}')
        try:
            request_data = Protocol.receive_message(client_sock)
            logging.info(f'action: receive_message | result: success | ip: {addr[0]}')

            result = self._handler.process_bet(request_data)

            Protocol.send_response(client_sock, result)
            logging.info(f'action: send_response | result: success | ip: {addr[0]}')
        except (OSError, ValueError, ConnectionAbortedError) as e:
            logging.error(f'action: client_handling | result: fail | ip: {addr[0]} | error: {e}')
        finally:
            logging.info(f'action: client_disconnect | result: success | ip: {addr[0]}')
            if client_sock in self._active_connections:
                self._active_connections.remove(client_sock)
            client_sock.close()

    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        self._active_connections.append(c)
        return c

    def __setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.__signal_handler)
        signal.signal(signal.SIGTERM, self.__signal_handler)

    def __signal_handler(self, sig, frame):
        logging.info(f'action: shutdown | result: in_progress | signal: {sig}')
        for client_sock in self._active_connections[:]:
            try:
                client_sock.close()
            except OSError as e:
                logging.error(f'action: close_client | result: fail | error: {e}')
        self._server_socket.close()
        logging.info('action: shutdown | result: success')
        sys.exit(0)