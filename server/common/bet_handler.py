import logging
import threading
from .utils import Bet, store_bets, load_bets, has_won
from .batch import Batch

class BetHandler:
    def process_batch(self, batch):
        try:
            logging.debug(f"action: process_batch | result: in_progress | batch_size: {len(batch.bets)}")
            
            store_bets(batch.bets)

            logging.debug(f'action: apuestas_almacadas | result: success | stored_count: {len(batch.bets)}')
            return {"status": "success", "message": "Batch stored successfully."}

        except Exception as e:
            logging.error(f"action: process_batch | result: fail | error: storage_error | details: {e}")
            return {"status": "error", "message": f"An unexpected error occurred while storing the batch: {e}"}

    def process_winners(self) -> dict[int, list[str]]:
        winners_by_agency: dict[int, list[str]] = {}
        for bet in load_bets():
            if has_won(bet):
                winners_by_agency.setdefault(bet.agency, []).append(bet.document)
        return winners_by_agency