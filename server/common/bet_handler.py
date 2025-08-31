import logging
import threading
from common.utils import Bet, store_bets, load_bets, has_won

class BetHandler:
    def __init__(self):
        self._lock = threading.Lock()
        self._winners = []

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

    def calculate_winners(self):
        with self._lock:
            all_bets = list(load_bets())
            
            if not all_bets:
                logging.warning("Winner calculation requested, but no bets were stored.")
                return

            self._winners = [bet for bet in all_bets if has_won(bet)]

        logging.info(f"Winner calculation complete. Found {len(self._winners)} total winners from {len(all_bets)} bets.")

    def get_winners_by_agency(self, agency_id: int) -> list[str]:
        logging.info(f"Retrieving winners for agency {agency_id}.")
        print([bet.agency for bet in self._winners])
        agency_winners = [bet.document for bet in self._winners if bet.agency == agency_id]
        return agency_winners