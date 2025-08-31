import socket
import logging
import signal
import threading

from .protocol import Protocol, ProtocolError
from .bet_handler import BetHandler

class Server:
    """A concurrent TCP server using a Listener/Worker threading model."""

    def __init__(self, port, listen_backlog, client_count):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = False
        self._handler = BetHandler()
        self._active_threads = []

        self._clients_finished_count = 0
        self._client_count = client_count
        self._state_lock = threading.Lock()
        self._draw_event = threading.Event()

        self.__setup_signal_handlers()

    def run(self):
        self._running = True
        logging.info(f"Server starting.")

        while self._running:
            try:
                client_sock, addr = self._server_socket.accept()
                
                worker_thread = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_sock, addr)
                )
                self._active_threads.append(worker_thread)
                worker_thread.start()

                self._active_threads = [t for t in self._active_threads if t.is_alive()]

            except OSError:
                if self._running:
                    logging.error("Error accepting connection.")
                else:
                    logging.info("Server socket closed, listener thread shutting down.")
                break

    def _handle_client_connection(self, client_sock, addr):
        client_agency = ""
        logging.info(f'action: client_connection | result: success | ip: {addr[0]}')
        with client_sock:
            try:
                while self._running:
                    batch_data = Protocol.receive_batch(client_sock)
                    if not batch_data:
                        logging.info(f'action: client_connection | result: success | ip: {addr[0]} | status: client finished sending bets')
                        break
                    
                    if batch_data and not client_agency:
                        client_agency = batch_data[0]['agency']

                    result = self._handler.process_batch(batch_data)
                    log_level = logging.INFO if result["status"] == "success" else logging.ERROR
                    logging.log(log_level, f'action: apuesta_recibida | result: {result["status"]} | cantidad: {len(batch_data)}')
                    Protocol.send_response(client_sock, result)

                logging.info(f"Client {addr[0]} ({client_agency}) is waiting for the lottery draw.")
                self._handle_client_finished()
                self._draw_event.wait()

                winners = self._handler.get_winners_by_agency(int(client_agency))
                if winners:
                    Protocol.send_winners(client_sock, winners)
                    logging.info(f'action: consulta_ganadores | result: success | ip: {addr[0]} | agency: {client_agency}')
                else:
                    logging.warning(f"No clients from agency {client_agency} won.")

            except (ConnectionAbortedError, ProtocolError, OSError) as e:
                logging.error(f'action: client_handling | result: fail | ip: {addr[0]} | error: {e}')
        
        logging.info(f'action: client_disconnect | result: success | ip: {addr[0]}')

    def _handle_client_finished(self):
        with self._state_lock:
            if self._draw_event.is_set():
                return

            self._clients_finished_count += 1
            logging.info(f"Client finished. Total finished: {self._clients_finished_count}/{self._client_count}")

            if self._clients_finished_count >= self._client_count:
                self._perform_draw()

    def _perform_draw(self):
        logging.info("All clients have finished. Performing lottery draw...")
        self._handler.calculate_winners()
        logging.info('action: sorteo | result: success')
        self._draw_event.set()
    
    def __setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, sig, frame):
        logging.info(f'action: shutdown | result: in_progress | signal: {sig}')
        self._running = False
        self._server_socket.close()
        for thread in self._active_threads:
            thread.join()