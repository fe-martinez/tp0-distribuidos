import logging
import threading
from .utils import Bet, store_bets, load_bets, has_won
from .batch import Batch

class BetHandler:
    def __init__(self):
        self._lock = threading.Lock()
        self._winners = []

    def process_batch(self, batch):
        try:
            logging.debug(f"action: process_batch | result: in_progress | batch_size: {len(batch.bets)}")
            
            with self._lock:
                store_bets(batch.bets)

            logging.debug(f'action: apuestas_almacenadas | result: success | stored_count: {len(batch.bets)}')
            return {"status": "success", "message": "Batch stored successfully."}

        except Exception as e:
            logging.error(f"action: process_batch | result: fail | error: storage_error | details: {e}")
            return {"status": "error", "message": f"An unexpected error occurred while storing the batch: {e}"}

    def calculate_winners(self):
        with self._lock:
            all_bets = list(load_bets())
            if not all_bets:
                logging.warning("Winner calculation requested, but no bets were stored.")
                return
            self._winners = [bet for bet in all_bets if has_won(bet)]
        logging.info(f"Winner calculation complete. Found {len(self._winners)} total winners.")

    def get_winners_by_agency(self, agency_id):
        agency_id_int = int(agency_id)
        return [bet.document for bet in self._winners if bet.agency == agency_id_int]