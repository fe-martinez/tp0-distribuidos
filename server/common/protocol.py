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

    def receive_batch(client_sock: socket.socket) -> list[dict[str, str]]:
        """Receive and parse a complete batch of bets from the client socket."""
        header = Protocol._read_line(client_sock)
        header_parts = header.split(Protocol.fieldSeparator)
        if len(header_parts) != 2:
            raise ProtocolError(f"Invalid batch header format: got {header}")

        agency_id, num_bets_str = header_parts
        try:
            num_bets = int(num_bets_str)
        except ValueError:
            raise ProtocolError(f"Invalid number of bets in header: '{num_bets_str}'")

        bets = []
        for _ in range(num_bets):
            bet_line = Protocol._read_line(client_sock)
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