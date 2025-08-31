import socket
import logging
import signal

from .protocol import Protocol, ProtocolError
from .bet_handler import BetHandler

class Server:
    def __init__(self, port, listen_backlog, client_count):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._handler = BetHandler()
        self._client_count = client_count
        self._client_connections = []
        self.__setup_signal_handlers()

    def run(self):
        logging.info(f"Connection phase: Waiting for {self._client_count} clients to connect.")
        for i in range(self._client_count):
            try:
                client_sock, addr = self._server_socket.accept()
                logging.info(f"Accepted connection from {addr[0]} ({i+1}/{self._client_count})")
                self._client_connections.append({"socket": client_sock, "address": addr, "agency": ""})
            except OSError:
                logging.error("Server socket closed during connection phase.")
                return

        logging.info("Processing phase: Handling clients one by one.")
        for conn_info in self._client_connections:
            self._handle_client_bets(conn_info)

        logging.info("All clients have finished sending bets. Performing draw...")
        self._handler.calculate_winners()
        logging.info('action: sorteo | result: success')

        logging.info("Sending results back to all clients.")
        for conn_info in self._client_connections:
            self._send_client_results(conn_info)

        logging.info("All results sent. Shutting down.")
        self._server_socket.close()

    def _handle_client_bets(self, conn_info):
        client_sock = conn_info["socket"]
        addr = conn_info["address"]
        logging.info(f'Processing bets for client {addr[0]}')
        
        try:
            while True:
                batch_data = Protocol.receive_batch(client_sock)
                if not batch_data:
                    logging.info(f'Client {addr[0]} finished sending bets.')
                    break
                
                if not conn_info["agency"]:
                    conn_info["agency"] = batch_data[0]['agency']

                result = self._handler.process_batch(batch_data)
                Protocol.send_response(client_sock, result)
        except (ProtocolError, OSError, ConnectionAbortedError) as e:
            logging.error(f'action: receive_bets | result: fail | ip: {addr[0]} | error: {e}')

    def _send_client_results(self, conn_info):
        client_sock = conn_info["socket"]
        addr = conn_info["address"]
        agency = conn_info["agency"]

        with client_sock:
            try:
                winners = self._handler.get_winners_by_agency(int(agency))
                Protocol.send_winners(client_sock, winners or [])
                logging.info(f'action: sent_winners | result: success | ip: {addr[0]} | agency: {agency}')
                client_sock.recv(1024) # Wait for client to close
            except (OSError, ProtocolError) as e:
                logging.error(f'action: send_results | result: fail | ip: {addr[0]} | error: {e}')

    def __setup_signal_handlers(self):
        signal.signal(signal.SIGINT, lambda s, f: self._server_socket.close())
        signal.signal(signal.SIGTERM, lambda s, f: self._server_socket.close())