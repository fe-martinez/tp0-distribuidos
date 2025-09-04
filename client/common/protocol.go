package common

import (
	"bytes"
	"fmt"
	"io"
	"net"
	"strings"
	"time"
)

const (
	ConnectionTimeout = 10 * time.Second
	ReadTimeout       = 5 * time.Second
)

type Response struct {
	Status  string
	Message string
}

type ProtocolError struct {
	Message string
	Err     error
}

func (e ProtocolError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("protocol error: %s: %v", e.Message, e.Err)
	}
	return fmt.Sprintf("protocol error: %s", e.Message)
}

func (e ProtocolError) Unwrap() error {
	return e.Err
}

func writeAll(conn net.Conn, msg []byte) error {
	totalSent := 0
	for totalSent < len(msg) {
		sent, err := conn.Write(msg[totalSent:])
		if err != nil {
			return fmt.Errorf("failed to write data: %w", err)
		}
		totalSent += sent
	}
	return nil
}

func readUntilDelimiter(conn net.Conn, delimiter byte) ([]byte, error) {
	buffer := make([]byte, 1024)
	var responseBuf bytes.Buffer

	conn.SetReadDeadline(time.Now().Add(ReadTimeout))

	for {
		bytesRead, err := conn.Read(buffer)
		if err != nil {
			if err == io.EOF && responseBuf.Len() > 0 {
				break
			}
			return nil, fmt.Errorf("failed to read data: %w", err)
		}

		responseBuf.Write(buffer[:bytesRead])

		if bytes.Contains(buffer[:bytesRead], []byte{delimiter}) {
			break
		}
	}
	return responseBuf.Bytes(), nil
}

func Send(conn net.Conn, payload []byte) (Response, error) {
	if err := writeAll(conn, payload); err != nil {
		return Response{}, ProtocolError{Message: "failed to send message", Err: err}
	}

	responseBytes, err := readUntilDelimiter(conn, '\n')
	if err != nil {
		return Response{}, ProtocolError{Message: "failed to receive response", Err: err}
	}

	responseStr := string(responseBytes)
	parts := strings.Split(strings.TrimSpace(responseStr), ";")
	if len(parts) != 2 {
		return Response{}, ProtocolError{
			Message: fmt.Sprintf("invalid server response format: expected 2 fields, got %d", len(parts)),
		}
	}

	return Response{
		Status:  strings.TrimSpace(parts[0]),
		Message: strings.TrimSpace(parts[1]),
	}, nil
}
