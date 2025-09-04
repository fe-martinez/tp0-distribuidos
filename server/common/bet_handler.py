import logging
import threading
from .utils import Bet, store_bets, load_bets, has_won
from .batch import Batch

class BetHandler:
    def __init__(self):
        self._lock = threading.Lock()

    def process_batch(self, batch):
        try:
            logging.debug(f"action: process_batch | result: in_progress | batch_size: {len(batch.bets)}")
            
            with self._lock:
                store_bets(batch.bets)

            logging.debug(f'action: apuestas_almacadas | result: success | stored_count: {len(batch.bets)}')
            return {"status": "success", "message": "Batch stored successfully."}

        except Exception as e:
            logging.error(f"action: process_batch | result: fail | error: storage_error | details: {e}")
            return {"status": "error", "message": f"An unexpected error occurred while storing the batch: {e}"}

    def get_winners_by_agency(self, agency_id_str):
        try:
            agency_id = int(agency_id_str)
            winners = []
            for bet in load_bets():
                if bet.agency == agency_id and has_won(bet):
                    winners.append(bet.document)
            return winners
        except (ValueError, TypeError):
            logging.warning(f"Could not convert agency ID '{agency_id_str}' to an integer.")
            return []