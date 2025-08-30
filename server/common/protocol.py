import logging
import socket

class ProtocolError(Exception):
    pass

class Protocol:
    encoding = 'utf-8'
    bufferSize = 1024
    messageDelimiter = '\n'
    fieldSeparator = ';'

    def _read_line(client_sock: socket.socket) -> str:
        chunks = []
        while True:
            try:
                chunk = client_sock.recv(Protocol.bufferSize).decode(Protocol.encoding)
            except UnicodeDecodeError as e:
                raise ProtocolError(f"Invalid message encoding: {e}")
            
            if not chunk:
                raise ConnectionAbortedError("Client closed the connection.")
            
            chunks.append(chunk)
            if Protocol.messageDelimiter in chunk:
                break
        
        return ''.join(chunks).strip()
    
    # Header format: AGENCY_ID;NUM_BETS
    # Bet format: FIRST_NAME;LAST_NAME;DOCUMENT;BIRTHDATE;NUMBER
    # Example batch:
    # AGENCY1;3\n
    # John;Doe;123456;1990-01-01;42\n
    # Jane;Smith;654321;1985-05-15;7\n
    # Alice;Johnson;111222;1978-12-30;19\n
    def __isHeader(parts: list[str]) -> bool:
        if len(parts) != 2:
            return False
        agency_id, num_bets_str = parts
        if not agency_id or not num_bets_str.isdigit():
            return False
        return True

    def receive_batch(client_sock: socket.socket) -> list[dict[str, str]]:
        """Receive and parse a complete batch of bets from the client socket."""
        line = Protocol._read_line(client_sock)
        objects = line.split(Protocol.messageDelimiter)
        header = objects[0].split(Protocol.fieldSeparator)

        if not Protocol.__isHeader(header):
            raise ProtocolError(f"Invalid batch header format: got {line}")

        agency_id, num_bets_str = header
        try:
            num_bets = int(num_bets_str)
        except ValueError:
            raise ProtocolError(f"Invalid number of bets in header: '{num_bets_str}'")

        bets = []
        for bet_line in objects[1:]:
            fields = bet_line.split(Protocol.fieldSeparator)
            if len(fields) != 5:
                raise ProtocolError(f"Invalid bet format: expected 5 fields, got {len(fields)}")
            
            bet_data = {
                "agency": agency_id.strip(),
                "firstName": fields[0].strip(),
                "lastName": fields[1].strip(),
                "document": fields[2].strip(),
                "birthdate": fields[3].strip(),
                "number": fields[4].strip()
            }
            bets.append(bet_data)
        
        logging.info(f'action: receive_batch | result: success | ip: {client_sock.getpeername()[0]} | batch_size: {len(bets)}')
        return bets

    def send_response(client_sock: socket.socket, response: dict[str, str]) -> None:
        """Send a response message to the client socket (this function remains the same)."""
        if 'status' not in response or 'message' not in response:
            raise ValueError("Response must contain 'status' and 'message' fields")

        response_str = f"{response['status']}{Protocol.fieldSeparator}{response['message']}{Protocol.messageDelimiter}"
        logging.debug(f"Sending response: {response_str.strip()}")
        
        try:
            client_sock.sendall(response_str.encode(Protocol.encoding))
        except socket.error as e:
            raise ProtocolError(f"Failed to send response: {e}")