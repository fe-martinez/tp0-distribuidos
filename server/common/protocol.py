import logging

class Protocol:
    def receive_message(client_sock) -> dict:
        chunks = []
        while True:
            chunk = client_sock.recv(1024).decode('utf-8')
            if not chunk:
                raise ConnectionAbortedError("Client closed the connection.")
            chunks.append(chunk)
            if '\n' in chunk:
                break
        
        full_message = ''.join(chunks).strip()

        fields = full_message.split(';')
        if len(fields) != 6:
            raise ValueError(f"Invalid message format: expected 6 fields, got {len(fields)}")

        return {
            "agency": fields[0],
            "firstName":  fields[1],
            "lastName":  fields[2],
            "document": fields[3],
            "birthdate": fields[4],
            "number":   fields[5]
        }

    def send_response(client_sock, response: str):
        response_str = f"{response}\n"
        logging.debug(f"Sending response: {response_str.strip()}")
        client_sock.sendall(response_str.encode('utf-8'))