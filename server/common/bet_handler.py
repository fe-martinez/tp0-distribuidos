import logging
from common.utils import Bet, store_bets

class BetHandler:
    def process_bet(self, bet_data: dict):
        try:
            logging.info(f"action: process_bet | result: in_progress")
            
            required_keys = ['firstName', 'lastName', 'document', 'birthdate', 'agency', 'number']
            if not all(key in bet_data for key in required_keys):
                raise ValueError("Missing required fields after protocol parsing.")

            bet = Bet(
                first_name=bet_data['firstName'],
                last_name=bet_data['lastName'],
                document=bet_data['document'],
                birthdate=bet_data['birthdate'],
                agency=bet_data['agency'],
                number=bet_data['number']
            )
            
            store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
            response = {"status": "success", "message": "Bet stored successfully."}
            return response

        except (ValueError, TypeError) as e:
            logging.error(f"action: process_bet | result: fail | error: {e}")
            return {"status": "error", "message": f"Error processing bet: {e}"}