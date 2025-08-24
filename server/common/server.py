import socket
import logging
import signal
import sys

from server.common.utils import Bet, store_bets


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._active_connections = []

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        self.setup_signal_handlers()

        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = self.__read_message(client_sock)
            addr = client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')

            fields = msg.split(';')
            if len(fields) < 6:
                raise ValueError("Invalid message format")
            
            bet = Bet(fields[0], fields[1], fields[2], fields[3], fields[4], fields[5])
            print(f'action: apuesta_enviada | result: success | dni: {bet.document} | numero: {bet.number}')
            store_bets([bet])
            client_sock.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error(f'action: receive_message | result: fail | error: {e}')
        finally:
            if client_sock in self._active_connections:
                self._active_connections.remove(client_sock)
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        self._active_connections.append(c)
        return c
    
    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        logging.info(f'action: shutdown | result: in_progress | signal: {sig}')
        
        for client_sock in self._active_connections[:]:
            try:
                client_sock.close()
                self._active_connections.remove(client_sock)
                logging.info(f'action: close_client | result: success | client: {client_sock.getpeername()[0]}')
            except OSError as e:
                logging.error(f'action: close_client | result: fail | error: {e}')
        
        self._server_socket.close()
        logging.info('action: shutdown | result: success')
        sys.exit(0)

    def __read_message(self, client_sock):
        """
        Read message from a specific client socket

        If a problem arises in the communication with the client, the
        client socket will be closed
        """
        chunks = []
        while True:
            chunk = client_sock.recv(1024)
            if not chunk:
                break
            chunks.append(chunk.decode('utf-8'))
        return ''.join(chunks).strip()
