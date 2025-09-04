import logging
import socket


class ProtocolError(Exception):
    pass


class Protocol:
    expectedFields = 6
    encoding = 'utf-8'
    bufferSize = 1024
    messageDelimiter = b'\n'
    fieldSeparator = ';'

    def receive_message(client_sock):
        chunks = bytearray()
        while True:
            chunk = client_sock.recv(Protocol.bufferSize)
            if not chunk:
                raise ConnectionAbortedError("Client closed the connection.")
            chunks += chunk
            nl = chunks.find(Protocol.messageDelimiter)
            if nl != -1:
                line = bytes(chunks[:nl])
                text = line.decode(Protocol.encoding)
                return Protocol.parse_bet_line(text)
    
    def parse_bet_line(line: str) -> dict[str, str]:
        text = line.strip()
        if not text:
            raise ProtocolError("Empty message received")

        fields = [f.strip() for f in text.split(Protocol.fieldSeparator)]
        if len(fields) != Protocol.expectedFields:
            raise ProtocolError(
                f"Invalid message format: expected {Protocol.expectedFields} fields, got {len(fields)}"
            )

        try:
            int(fields[5])
        except ValueError:
            raise ProtocolError(f"Invalid number field: '{fields[5]}' is not a valid integer")

        return {
            "agency":    fields[0],
            "firstName": fields[1],
            "lastName":  fields[2],
            "document":  fields[3],
            "birthdate": fields[4],
            "number":    fields[5],
        }

    def send_response(client_sock: socket.socket, response: dict[str, str]) -> None:
        if 'status' not in response or 'message' not in response:
            raise ValueError("Response must contain 'status' and 'message' fields")

        response_str = f"{response['status']}{Protocol.fieldSeparator}{response['message']}\n"

        logging.debug(f"Sending response: {response_str}")
        try:
            client_sock.sendall(response_str.encode(Protocol.encoding))
        except socket.error as e:
            raise ProtocolError(f"Failed to send response: {e}")