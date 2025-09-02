import socket
import logging
import signal
import multiprocessing

from .protocol import Protocol, ProtocolError
from .bet_handler import BetHandler

class Server:
    def __init__(self, port, listen_backlog, client_count):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = False
        self._client_count = client_count
        self._active_processes = []
        
        self._lock = multiprocessing.Lock()
        self._draw_barrier = multiprocessing.Barrier(self._client_count, action=self._perform_draw)
        self.__setup_signal_handlers()

    def run(self):
        self._running = True
        logging.info(f"Server starting. Awaiting {self._client_count} clients.")

        while self._running:
            try:
                client_sock, addr = self._server_socket.accept()
                
                worker_process = multiprocessing.Process(
                    target=self._handle_client_connection,
                    args=(client_sock, addr, self._lock, self._draw_barrier)
                )
                self._active_processes.append(worker_process)
                worker_process.start()

                self._active_processes = [p for p in self._active_processes if p.is_alive()]

            except OSError:
                if self._running:
                    logging.error("Error accepting connection.")
                else:
                    logging.info("Server socket closed, listener shutting down.")
                break

        logging.info("action: server_shutdown | result: success")

    def _handle_client_connection(self, client_sock, addr, lock, barrier):
        client_agency = ""
        handler = BetHandler(lock)
        logging.info(f'action: client_connection | result: success | ip: {addr[0]}')
        
        with client_sock:
            try:
                while True:
                    batch_data = Protocol.receive_batch(client_sock)
                    if not batch_data:
                        logging.info(f'action: client_connection | result: success | ip: {addr[0]} | status: client finished sending bets')
                        break
                    
                    if not client_agency:
                        client_agency = batch_data[0]['agency']

                    result = handler.process_batch(batch_data)
                    log_level = logging.INFO if result["status"] == "success" else logging.ERROR
                    logging.log(log_level, f'action: apuesta_recibida | result: {result["status"]} | cantidad: {len(batch_data)}')
                    Protocol.send_response(client_sock, result)

                logging.info(f"Client {addr[0]} ({client_agency}) has finished sending bets. Waiting for other processes.")
                
                barrier.wait()
                winners = handler.get_winners_by_agency(int(client_agency))

                Protocol.send_winners(client_sock, winners or []) 
                logging.info(f'action: sent_winners | result: success | ip: {addr[0]} | agency: {client_agency}')

            except ConnectionAbortedError as e:
                logging.error(f'action: client_close | result: success | ip: {addr[0]} | error: {e}')
            except multiprocessing.ProcessError as e:
                logging.error(f'action: process_error | result: fail | ip: {addr[0]} | error: {e}')
            except (ProtocolError, OSError) as e:
                logging.error(f'action: client_handling | result: fail | ip: {addr[0]} | error: {e}')
        
        logging.info(f'action: client_disconnect | result: success | ip: {addr[0]}')

    def _perform_draw(self):
        logging.info("All clients have finished. Performing lottery draw...")
        handler = BetHandler(multiprocessing.Lock())
        handler.calculate_winners()
        logging.info('action: sorteo | result: success')
    
    def __setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, sig, frame):
        logging.info(f'action: shutdown | result: in_progress | signal: {sig}')
        self._running = False
        self._server_socket.close()
        self._draw_barrier.abort()
        for process in self._active_processes:
            process.join()