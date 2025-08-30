import logging
from common.utils import Bet, store_bets

class BetHandler:
    def process_batch(self, batch_data: list[dict]):
        """
        Processes a list of bets, stores them, and returns a single response.
        This version includes improved error handling and is more concise.
        """
        try:
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
            except (KeyError, ValueError, TypeError) as e:
                logging.error(f"action: process_batch | result: fail | error: invalid_bet_data | details: {e}")
                return {"status": "error", "message": f"Invalid data in batch: {e}"}

            store_bets(bets_to_store)

            logging.debug(f'action: apuestas_almacenadas | result: success | stored_count: {len(bets_to_store)}')
            return {"status": "success", "message": "Batch stored successfully."}
        except Exception as e:
            logging.error(f"action: process_batch | result: fail | error: {e}")
            return {"status": "error", "message": f"An unexpected error occurred while processing the batch: {e}"}