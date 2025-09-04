# FILE: common/batch.py

from .utils import Bet

class Batch:
    def __init__(self, agency_id, bets):
        self.agency_id = agency_id
        self.bets = bets

    def from_payload(cls, payload_bytes, encoding, separator):
        try:
            payload_str = payload_bytes.decode(encoding)
        except UnicodeDecodeError:
            raise ValueError("Invalid message encoding.")

        lines = [line for line in payload_str.strip().split('\n') if line]
        if not lines:
            raise ValueError("Empty batch payload.")

        header_parts = lines[0].split(separator)
        if len(header_parts) != 2 or not header_parts[1].isdigit():
            raise ValueError(f"Invalid batch header format: got '{lines[0]}'")
        
        agency_id, num_bets_str = [part.strip() for part in header_parts]

        bet_lines = lines[1:]
        if len(bet_lines) != int(num_bets_str):
            raise ValueError(f"Batch size mismatch: header indicates {num_bets_str}, but received {len(bet_lines)}.")

        parsed_bets = []
        for line in bet_lines:
            fields = line.strip().split(separator)
            if len(fields) != 5:
                raise ValueError(f"Invalid bet format in line: '{line}'")
            
            parsed_bets.append(
                Bet(
                    agency=agency_id,
                    first_name=fields[0],
                    last_name=fields[1],
                    document=fields[2],
                    birthdate=fields[3],
                    number=fields[4]
                )
            )
        
        return cls(agency_id, parsed_bets)