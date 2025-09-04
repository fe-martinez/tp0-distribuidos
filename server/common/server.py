import socket
import logging
import signal
from .protocol import Protocol, ProtocolError
from .bet_handler import BetHandler
from .batch import Batch

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
        logging.info(f"action: server_start | result: success | port: {self._server_socket.getsockname()[1]} | max_clients: {self._client_count}")
        for _ in range(self._client_count):
            try:
                client_sock, addr = self._server_socket.accept()
                logging.info(f'action: client_connection | result: success | ip: {addr[0]}')
                self._client_connections.append({"socket": client_sock, "address": addr, "agency": ""})
            except OSError:
                logging.error("action: server_accept | result: fail | error: accept_failed")
                return

        logging.info("action: all_clients_connected | result: success")
        for conn_info in self._client_connections:
            self._handle_client_bets(conn_info)

        logging.info("action: all_clients_finished | result: success")
        self._handler.calculate_winners()   
        logging.info('action: sorteo | result: success')

        for conn_info in self._client_connections:
            self._send_client_results(conn_info)
        logging.info("action: finished_sending_results | result: success")

        self.__shutdown()

    def _handle_client_bets(self, conn_info):
        client_sock = conn_info["socket"]
        addr = conn_info["address"]
        
        try:
            while True:
                payload_bytes = Protocol.receive(client_sock)
                if payload_bytes == b'END':
                    logging.info(f'action: client_connection | result: success | ip: {addr[0]} | status: client finished sending bets')
                    break
                if payload_bytes == b'':
                    logging.info(f"action: client_connection | result: success | ip: {addr[0]} | status: client sent empty payload")
                    continue
                
                batch = Batch.from_payload(payload_bytes, Protocol.encoding, Protocol.field_separator)
                if not conn_info["agency"]:
                    conn_info["agency"] = batch.agency_id
                
                result = self._handler.process_batch(batch)
                
                log_level = logging.INFO if result["status"] == "success" else logging.ERROR
                logging.log(log_level, f'action: apuesta_recibida | result: {result["status"]} | cantidad: {len(batch.bets)}')

                response_str = f"{result['status']}{Protocol.field_separator}{result['message']}"
                Protocol.send(client_sock, response_str.encode(Protocol.encoding))
            
            agency = conn_info.get("agency", "N/A")
            logging.info(f"action: client_finished | result: success | ip: {addr[0]} | agency: {agency}")

        except (ValueError, ProtocolError, OSError, ConnectionAbortedError) as e:
            logging.error(f'action: client_handling | result: fail | ip: {addr[0]} | error: {e}')

    def _send_client_results(self, conn_info):
        client_sock = conn_info["socket"]
        addr = conn_info["address"]
        agency = conn_info["agency"]

        with client_sock:
            try:
                winners = self._handler.get_winners_by_agency(agency)
                if not winners:
                    winners_payload_str = "NO_WINNERS"
                else:
                    winners_payload_str = Protocol.field_separator.join(winners)
                
                Protocol.send(client_sock, winners_payload_str.encode(Protocol.encoding))
                logging.info(f'action: send_winners | result: success | ip: {addr[0]} | agency: {agency}')
                
            except (OSError, ProtocolError) as e:
                logging.error(f'action: client_handling | result: fail | ip: {addr[0]} | error: {e}')

    def __setup_signal_handlers(self):
        signal.signal(signal.SIGINT, lambda s, f: self.__shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.__shutdown())

    def __shutdown(self):
        logging.info('action: shutdown | result: in_progress')

        for conn_info in self._client_connections[:]:
            try:
                logging.info(f"Closing connection with {conn_info['address'][0]}")
                conn_info["socket"].close()
            except (OSError, socket.error) as e:
                logging.warning(f'action: close_client | result: success | client already_closed')

        self._server_socket.close()
        logging.info('action: shutdown | result: success')