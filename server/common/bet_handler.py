import logging
from .utils import Bet, store_bets

class BetHandler:
    def _parse_bet_line(self, line: str) -> dict:
        text = line.strip()
        if not text:
            raise Exception("Empty bet line")

        fields = [f.strip() for f in text.split(';')]
        if len(fields) != 6:
            raise Exception(f"Invalid message format: expected 6 fields, got {len(fields)}")

        try:
            int(fields[5])
        except ValueError:
            raise Exception(f"Invalid number field: '{fields[5]}' is not a valid integer")

        return {
            "agency":    fields[0],
            "firstName": fields[1],
            "lastName":  fields[2],
            "document":  fields[3],
            "birthdate": fields[4],
            "number":    fields[5],
        }


    def process_bet(self, raw_bet_data: str) -> dict:
        try:
            logging.info(f"action: process_bet | result: in_progress")
            
            bet_data = self._parse_bet_line(raw_bet_data)
            
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
            
            return {"status": "success", "message": "Bet stored successfully."}

        except (ValueError, TypeError) as e:
            logging.error(f"action: process_bet | result: fail | error: {e}")
            return {"status": "error", "message": f"Error processing bet: {e}"}