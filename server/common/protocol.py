import logging
import socket

class ProtocolError(Exception):
    pass

class Protocol:
    encoding = 'utf-8'
    bufferSize = 1024
    header_size = 8
    messageDelimiter = '\n'
    fieldSeparator = ';'

    def _receive_all(client_sock: socket.socket, length: int) -> bytes:
        chunks = []
        bytes_received = 0
        while bytes_received < length:
            chunk = client_sock.recv(min(length - bytes_received, Protocol.bufferSize))
            if not chunk:
                break
            chunks.append(chunk)
            bytes_received += len(chunk)
        return b''.join(chunks)
    
    def _is_end_message(header_bytes: bytes) -> bool:
        return header_bytes.decode(Protocol.encoding, errors='ignore').strip() == "END"

    def _parse_bet_line(line: str, agency_id: str) -> dict:
        fields = line.split(Protocol.fieldSeparator)
        if len(fields) != 5:
            raise ProtocolError(f"Invalid bet format: expected 5 fields, got {len(fields)} in '{line}'")
        
        return {
            "agency": agency_id.strip(),
            "firstName": fields[0].strip(),
            "lastName": fields[1].strip(),
            "document": fields[2].strip(),
            "birthdate": fields[3].strip(),
            "number": fields[4].strip()
        }

    def receive_batch(client_sock: socket.socket) -> list[dict[str, str]]:
        try:
            header_bytes = Protocol._receive_all(client_sock, Protocol.header_size)

            if Protocol._is_end_message(header_bytes):
                logging.info(f"Received END message from client {client_sock.getpeername()}")
                return []

            msg_len = int(header_bytes.decode(Protocol.encoding))
            
            if msg_len == 0:
                return []

            payload_bytes = Protocol._receive_all(client_sock, msg_len)
            payload_str = payload_bytes.decode(Protocol.encoding)

        except (UnicodeDecodeError, ValueError):
            raise ProtocolError("Invalid message encoding or content-length header.")

        lines = payload_str.strip().split(Protocol.messageDelimiter)
        header_parts = lines[0].split(Protocol.fieldSeparator)
        
        if len(header_parts) != 2 or not header_parts[0] or not header_parts[1].isdigit():
            raise ProtocolError(f"Invalid batch header format: got {lines[0]}")
        
        agency_id, num_bets_str = header_parts

        bet_lines = [line for line in lines[1:] if line]
        bets = [Protocol._parse_bet_line(line, agency_id) for line in bet_lines]

        if len(bets) != int(num_bets_str):
            raise ProtocolError(f"Batch size mismatch: header says {num_bets_str}, but payload has {len(bets)}.")
        
        return bets
    
    def send_response(client_sock: socket.socket, response: dict[str, str]) -> None:
        if 'status' not in response or 'message' not in response:
            raise ValueError("Response must contain 'status' and 'message' fields")

        response_str = f"{response['status']}{Protocol.fieldSeparator}{response['message']}{Protocol.messageDelimiter}"
        payload_bytes = response_str.encode(Protocol.encoding)
        header_bytes = f"{len(payload_bytes):0{Protocol.header_size}d}".encode(Protocol.encoding)
        full_message = header_bytes + payload_bytes
        
        try:
            client_sock.sendall(full_message)
        except socket.error as e:
            raise ProtocolError(f"Failed to send response: {e}")

    def send_winners(client_sock: socket.socket, winners: list[str]):
        if not winners:
            response_str = "NO_WINNERS"
        else:
            response_str = Protocol.fieldSeparator.join(winners)
        payload_bytes = response_str.encode(Protocol.encoding)
        header_bytes = f"{len(payload_bytes):0{Protocol.header_size}d}".encode(Protocol.encoding)
        full_message = header_bytes + payload_bytes
        
        try:
            client_sock.sendall(full_message)
        except socket.error as e:
            raise ProtocolError(f"Failed to send winner list: {e}")