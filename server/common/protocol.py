import socket

class ProtocolError(Exception):
    pass

class Protocol:
    encoding = 'utf-8'
    buffer_size = 1024
    message_delimiter = b'\n'
    field_separator = ';'

    def receive_message(client_sock: socket.socket) -> str:
        chunks = bytearray()
        while True:
            chunk = client_sock.recv(Protocol.buffer_size)
            if not chunk:
                raise ConnectionAbortedError("Client closed the connection.")
            chunks.extend(chunk)
            if Protocol.message_delimiter in chunks:
                line, _, _ = chunks.partition(Protocol.message_delimiter)
                return line.decode(Protocol.encoding)

    def send_response(client_sock: socket.socket, response: dict):
        if 'status' not in response or 'message' not in response:
            raise ValueError("Response must contain 'status' and 'message' fields")

        response_str = f"{response['status']}{Protocol.field_separator}{response['message']}\n"
        
        try:
            client_sock.sendall(response_str.encode(Protocol.encoding))
        except socket.error as e:
            raise ProtocolError(f"Failed to send response: {e}")