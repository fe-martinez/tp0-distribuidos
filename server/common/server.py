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
        self._clients_finished_count = 0
        self.__setup_signal_handlers()

    def run(self):
        logging.info(f"action: server_start | result: success | port: {self._server_socket.getsockname()[1]} | max_clients: {self._client_count}")
        for i in range(self._client_count):
            try:
                client_sock, addr = self._server_socket.accept()
                logging.info(f'action: client_connection | result: success | ip: {addr[0]}')
                self._client_connections.append({"socket": client_sock, "address": addr, "agency": ""})
            except OSError:
                logging.error("action: server_accept | result: fail | error: accept_failed")
                return

        logging.info("action: server_process | result: success | message: All clients connected. Handling bets sequentially.")
        for conn_info in self._client_connections:
            self._handle_client_bets(conn_info)

        logging.info("action: clients_finished | result: success | message: Proceeding to lottery draw.")
        self._handler.calculate_winners()   
        logging.info('action: sorteo | result: success')

        for conn_info in self._client_connections:
            self._send_client_results(conn_info)
        logging.info("action: sending_results | result: success")

        self._server_socket.close()

    def _handle_client_bets(self, conn_info):
        client_sock = conn_info["socket"]
        addr = conn_info["address"]
        
        try:
            while True:
                batch_data = Protocol.receive_batch(client_sock)
                if not batch_data:
                    logging.info(f'action: client_connection | result: success | ip: {addr[0]} | status: client finished sending bets')
                    break
                
                if not conn_info["agency"]:
                    conn_info["agency"] = batch_data[0]['agency']
                
                result = self._handler.process_batch(batch_data)
                log_level = logging.INFO if result["status"] == "success" else logging.ERROR
                logging.log(log_level, f'action: apuesta_recibida | result: {result["status"]} | cantidad: {len(batch_data)}')
                Protocol.send_response(client_sock, result)
            
            agency = conn_info.get("agency", "N/A")
            self._clients_finished_count += 1
            logging.info(f"action: client_finished | result: success | ip: {addr[0]} | agency: {agency} | total_finished: {self._clients_finished_count}/{self._client_count}")

        except (ProtocolError, OSError, ConnectionAbortedError) as e:
            logging.error(f'action: client_handling | result: fail | ip: {addr[0]} | error: {e}')

    def _send_client_results(self, conn_info):
        client_sock = conn_info["socket"]
        addr = conn_info["address"]
        agency = conn_info["agency"]

        with client_sock:
            try:
                winners = self._handler.get_winners_by_agency(int(agency))
                Protocol.send_winners(client_sock, winners or [])
                logging.info(f'action: send_winners | result: success | ip: {addr[0]} | agency: {agency}')
                client_sock.recv(1024)
            except (OSError, ProtocolError) as e:
                logging.error(f'action: client_handling | result: fail | ip: {addr[0]} | error: {e}')
        
        logging.info(f'action: client_disconnect | result: success | ip: {addr[0]}')

    def __setup_signal_handlers(self):
        signal.signal(signal.SIGINT, lambda s, f: self._server_socket.close())
        signal.signal(signal.SIGTERM, lambda s, f: self._server_socket.close())