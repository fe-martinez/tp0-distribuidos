import socket

class ProtocolError(Exception):
    pass

class Protocol:
    encoding = 'utf-8'
    buffer_size = 1024
    header_size = 8
    field_separator = ';'

    def _receive_all(client_sock, length):
        chunks = []
        bytes_received = 0
        while bytes_received < length:
            chunk = client_sock.recv(min(length - bytes_received, Protocol.buffer_size))
            if not chunk:
                break
            chunks.append(chunk)
            bytes_received += len(chunk)

        if bytes_received < length:
             raise ConnectionAbortedError("Socket connection broken.")
        return b''.join(chunks)

    def receive(client_sock):
        try:
            header_bytes = Protocol._receive_all(client_sock, Protocol.header_size)

            msg_len = int(header_bytes.decode(Protocol.encoding))
            if msg_len == 0:
                return b''
                
            return Protocol._receive_all(client_sock, msg_len)
        except (UnicodeDecodeError, ValueError):
            raise ProtocolError("Invalid header encoding or length.")

    def send(client_sock, payload_bytes):
        try:
            header_bytes = f"{len(payload_bytes):0{Protocol.header_size}d}".encode(Protocol.encoding)
            full_message = header_bytes + payload_bytes
            client_sock.sendall(full_message)
        except socket.error as e:
            raise ProtocolError(f"Failed to send message: {e}")