import logging
import socket


class ProtocolError(Exception):
    pass


class Protocol:
    expectedFields = 6
    encoding = 'utf-8'
    bufferSize = 1024
    messageDelimiter = '\n'
    fieldSeparator = ';'

    def receive_message(client_sock: socket.socket) -> dict[str, str]:
        """Receive and parse a bet message from the client socket"""
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
        
        full_message = ''.join(chunks).strip()
        if not full_message:
            raise ProtocolError("Empty message received")

        fields = full_message.split(Protocol.fieldSeparator)
        if len(fields) != Protocol.expectedFields:
            raise ProtocolError(f"Invalid message format: expected {Protocol.expectedFields} fields, got {len(fields)}")

        try:
            int(fields[5])
        except ValueError:
            raise ProtocolError(f"Invalid number field: '{fields[5]}' is not a valid integer")

        return {
            "agency": fields[0].strip(),
            "firstName": fields[1].strip(),
            "lastName": fields[2].strip(),
            "document": fields[3].strip(),
            "birthdate": fields[4].strip(),
            "number": fields[5].strip()
        }

    def send_response(client_sock: socket.socket, response: dict[str, str]) -> None:
        """Send a response message to the client socket"""
        if 'status' not in response or 'message' not in response:
            raise ValueError("Response must contain 'status' and 'message' fields")

        response_str = f"{response['status']}{Protocol.fieldSeparator}{response['message']}{Protocol.messageDelimiter}"
        logging.debug(f"Sending response: {response_str.strip()}")
        
        try:
            client_sock.sendall(response_str.encode(Protocol.encoding))
        except socket.error as e:
            raise ProtocolError(f"Failed to send response: {e}")