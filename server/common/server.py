import socket
import logging
import signal
import threading
from .protocol import Protocol, ProtocolError
from .bet_handler import BetHandler
from .batch import Batch

class Server:
    def __init__(self, port, listen_backlog, client_count):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = False
        self._handler = BetHandler()
        self._client_count = client_count
        self._active_clients = []
        self._clients_lock = threading.Lock()
        self._bets_lock = threading.Lock()
        self._draw_barrier = threading.Barrier(self._client_count, action=self.__on_ready_to_draw)
        self._winners = {}
        self.__setup_signal_handlers()

    def run(self):
        self._running = True
        logging.info(f"action: server_start | result: success | expected_clients: {self._client_count}")
        self._server_socket.settimeout(1.0)

        while self._running and len(self._active_clients) < self._client_count:
            try:
                client_sock, addr = self._server_socket.accept()
                worker_thread = threading.Thread(target=self._handle_client_connection, args=(client_sock, addr))
                with self._clients_lock:
                    self._active_clients.append((worker_thread, client_sock))
                worker_thread.start()
            except socket.timeout:
                continue
            except OSError as e:
                if self._running:
                    logging.error(f"action: server_accept | result: fail | error: {e}")
                else:
                    logging.info("action: listener_shutdown | result: success")
                break

        logging.info("action: waiting for client processing | result: success")
        with self._clients_lock:
            threads_to_join = [client[0] for client in self._active_clients]

        for t in threads_to_join:
            t.join()
        
        # In this case client sockets should already be closed by the use of 'with' in _handle_client_connection

        try:
            self._server_socket.close()
        except OSError:
            pass
    
        logging.info("action: server_shutdown | result: success")

    def _handle_client_connection(self, client_sock, addr):
        logging.info(f"action: client_connection | result: success | ip: {addr[0]}")
        client_agency = None
        client_sock.settimeout(10.0)

        with client_sock:
            try:
                while True:
                    payload_bytes = Protocol.receive(client_sock)
                    if payload_bytes == b'END':
                        logging.info(f"action: client_connection | result: success | ip: {addr[0]} | status: finished_sending_bets")
                        break

                    try:
                        batch = Batch.from_payload(payload_bytes, Protocol.encoding, Protocol.field_separator)
                    except ValueError as e:
                        logging.error(f"action: apuesta_recibida | result: fail | cantidad: 0")
                        error_response_str = f"error{Protocol.field_separator}Invalid batch format: {e}"
                        Protocol.send(client_sock, error_response_str.encode(Protocol.encoding))
                        continue

                    if client_agency is None:
                        client_agency = batch.agency_id

                    with self._bets_lock:
                        result = self._handler.process_batch(batch)

                    log_level = logging.INFO if result["status"] == "success" else logging.ERROR
                    logging.log(log_level, f"action: apuesta_recibida | result: {result['status']} | cantidad: {len(batch.bets)}")
                    
                    response_str = f"{result['status']}{Protocol.field_separator}{result['message']}"
                    Protocol.send(client_sock, response_str.encode(Protocol.encoding))

                logging.info(f"action: client_waiting_for_draw | result: success | ip: {addr[0]} | agency: {client_agency}")
                self._draw_barrier.wait(30.0)
                
                agency_key = int(client_agency) if client_agency is not None else 0
                winners_docs = self._winners.get(agency_key, [])
                winners_payload_str = "NO_WINNERS" if not winners_docs else Protocol.field_separator.join(winners_docs)
                Protocol.send(client_sock, winners_payload_str.encode(Protocol.encoding))
                logging.info(f"action: sent_winners | result: success | ip: {addr[0]} | agency: {client_agency}")

            except (ValueError, ProtocolError, ConnectionAbortedError) as e:
                logging.error(f"action: client_handling | result: fail | ip: {addr[0]} | error: {e}")
            except threading.BrokenBarrierError:
                logging.info(f"action: barrier_broken | result: fail | ip: {addr[0]}")
            except OSError as e:
                logging.error(f"action: socket_error | result: fail | ip: {addr[0]} | error: {e}")

        logging.info(f"action: client_disconnect | result: success | ip: {addr[0]}")

    def __on_ready_to_draw(self):
        self._winners = self._handler.process_winners()
        logging.info("action: sorteo | result: success")

    def __setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.__shutdown)
        signal.signal(signal.SIGTERM, self.__shutdown)

    def __shutdown(self, sig, frame):
        logging.info(f"action: shutdown | result: in_progress | signal: {sig}")
        self._running = False
        try:
            self._draw_barrier.abort()
        except Exception:
            pass

        try:
            self._server_socket.close()
        except Exception as e:
            logging.error(f"action: server_socket_close | result: fail | error: {e}")
        
        logging.info("action: shutdown | result: in_progress | message: joining active client threads")
        with self._clients_lock:
            for thread, sock in self._active_clients:
                if thread.is_alive():
                    thread.join(timeout=1.0)
                try:
                    sock.close()
                except Exception:
                    pass

        logging.info("action: shutdown | result: success")