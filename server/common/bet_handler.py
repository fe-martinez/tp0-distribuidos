import logging
import threading
from common.utils import Bet, store_bets, load_bets, has_won

class BetHandler:
    def __init__(self):
        self._lock = threading.Lock()

    def process_batch(self, batch_data: list[dict]):
        logging.debug(f"action: process_batch | result: in_progress | batch_size: {len(batch_data)}")
        try:
            bets_to_store = [
                Bet(
                    first_name=data['firstName'],
                    last_name=data['lastName'],
                    document=data['document'],
                    birthdate=data['birthdate'],
                    agency=data['agency'],
                    number=data['number']
                ) for data in batch_data
            ]

            with self._lock:
                store_bets(bets_to_store)

            logging.debug(f'action: apuestas_almacenadas | result: success | stored_count: {len(bets_to_store)}')
            return {"status": "success", "message": "Batch stored successfully."}

        except (KeyError, ValueError, TypeError) as e:
            logging.error(f"action: process_batch | result: fail | error: invalid_bet_data | details: {e}")
            return {"status": "error", "message": f"Invalid data in batch: {e}"}
        except Exception as e:
            logging.error(f"action: process_batch | result: fail | error: storage_error | details: {e}")
            return {"status": "error", "message": f"An unexpected error occurred while storing the batch: {e}"}

    def get_winners_by_agency(self, agency_id: int) -> list[str]:
        with self._lock:
            agency_winners = [bet.document for bet in load_bets() if bet.agency == agency_id and has_won(bet) ]
        return agency_winners