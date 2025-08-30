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
        """Helper function to reliably receive an exact number of bytes."""
        chunks = []
        bytes_received = 0
        while bytes_received < length:
            chunk = client_sock.recv(min(length - bytes_received, Protocol.bufferSize))
            if not chunk:
                raise ConnectionAbortedError("Socket connection broken before all data was received.")
            chunks.append(chunk)
            bytes_received += len(chunk)
        return b''.join(chunks)

    def receive_batch(client_sock: socket.socket) -> list[dict[str, str]]:
        try:
            header_bytes = Protocol._receive_all(client_sock, Protocol.header_size)
            msg_len = int(header_bytes.decode(Protocol.encoding))

            payload_bytes = Protocol._receive_all(client_sock, msg_len)
            payload_str = payload_bytes.decode(Protocol.encoding)

        except (UnicodeDecodeError, ValueError):
            raise ProtocolError("Invalid message encoding or content-length header.")
        except ConnectionAbortedError as e:
            logging.error(f"Connection lost while receiving batch: {e}")
            raise

        lines = payload_str.strip().split(Protocol.messageDelimiter)
        header_parts = lines[0].split(Protocol.fieldSeparator)
        
        if len(header_parts) != 2 or not header_parts[0] or not header_parts[1].isdigit():
            raise ProtocolError(f"Invalid batch header format: got {lines[0]}")
        
        agency_id, num_bets_str = header_parts

        bets = []
        for bet_line in lines[1:]:
            if not bet_line:
                continue
            
            fields = bet_line.split(Protocol.fieldSeparator)
            if len(fields) != 5:
                raise ProtocolError(f"Invalid bet format: expected 5 fields, got {len(fields)} in '{bet_line}'")
            
            bet_data = {
                "agency": agency_id.strip(),
                "firstName": fields[0].strip(),
                "lastName": fields[1].strip(),
                "document": fields[2].strip(),
                "birthdate": fields[3].strip(),
                "number": fields[4].strip()
            }
            bets.append(bet_data)
        
        logging.debug(f'action: receive_batch | result: success | ip: {client_sock.getpeername()[0]} | batch_size: {len(bets)}')
        return bets

    def send_response(client_sock: socket.socket, response: dict[str, str]) -> None:
        """Send a response message to the client socket, framed with a content-length header."""
        if 'status' not in response or 'message' not in response:
            raise ValueError("Response must contain 'status' and 'message' fields")

        response_str = f"{response['status']}{Protocol.fieldSeparator}{response['message']}{Protocol.messageDelimiter}"
        payload_bytes = response_str.encode(Protocol.encoding)
        header_bytes = f"{len(payload_bytes):0{Protocol.header_size}d}".encode(Protocol.encoding)
        
        full_message = header_bytes + payload_bytes
        logging.debug(f"Sending response: {response_str.strip()}")
        try:
            client_sock.sendall(full_message)
        except socket.error as e:
            raise ProtocolError(f"Failed to send response: {e}")