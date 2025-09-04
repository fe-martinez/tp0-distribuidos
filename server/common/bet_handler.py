import logging
from .utils import store_bets
from .batch import Batch

class BetHandler:
    def process_batch(self, batch):
        try:
            logging.debug(f"action: process_batch | result: in_progress | batch_size: {len(batch.bets)}")
            
            store_bets(batch.bets)

            logging.debug(f'action: apuestas_almacenadas | result: success | stored_count: {len(batch.bets)}')
            return {"status": "success", "message": "Batch stored successfully."}
        
        except Exception as e:
            logging.error(f"action: process_batch | result: fail | error: {e}")
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}