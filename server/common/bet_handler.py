import logging
from common.utils import Bet, store_bets

class BetHandler:
    def process_batch(self, batch_data: list[dict]):
        """Processes a list of bets, stores them, and returns a single response."""
        try:
            logging.debug(f"action: process_batch | result: in_progress | batch_size: {len(batch_data)}")
            
            bets_to_store = []
            for bet_data in batch_data:
                bet = Bet(
                    first_name=bet_data['firstName'],
                    last_name=bet_data['lastName'],
                    document=bet_data['document'],
                    birthdate=bet_data['birthdate'],
                    agency=bet_data['agency'],
                    number=bet_data['number']
                )
                bets_to_store.append(bet)
            
            store_bets(bets_to_store)

            if bets_to_store:
                last_bet = bets_to_store[-1]
                logging.debug(f'action: apuestas_almacenadas | result: success | dni: {last_bet.document} | numero: {last_bet.number}')

            return {"status": "success", "message": "Batch stored successfully."}

        except (ValueError, TypeError) as e:
            logging.error(f"action: process_batch | result: fail | error: {e}")
            return {"status": "error", "message": f"Error processing batch: {e}"}