package common

import (
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"time"
)

const (
	ConnectionTimeout = 10 * time.Second
	ReadTimeout       = 5 * time.Second
	WriteTimeout      = 5 * time.Second
	HeaderSize        = 8
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

func writeAll(conn net.Conn, buf []byte) error {
	totalWritten := 0
	for totalWritten < len(buf) {
		n, err := conn.Write(buf[totalWritten:])
		if err != nil {
			return err
		}
		totalWritten += n
	}
	return nil
}

func Send(conn net.Conn, payload []byte) error {
	header := fmt.Sprintf("%0*d", HeaderSize, len(payload))
	fullMessage := append([]byte(header), payload...)

	if err := conn.SetWriteDeadline(time.Now().Add(WriteTimeout)); err != nil {
		return fmt.Errorf("failed to set write deadline: %w", err)
	}
	defer conn.SetWriteDeadline(time.Time{})

	if err := writeAll(conn, fullMessage); err != nil {
		return ProtocolError{Message: "failed to send message", Err: err}
	}
	return nil
}

func Receive(conn net.Conn, timeout time.Duration) ([]byte, error) {
	if err := conn.SetReadDeadline(time.Now().Add(timeout)); err != nil {
		return nil, fmt.Errorf("failed to set read deadline: %w", err)
	}
	defer conn.SetReadDeadline(time.Time{})

	headerBuf := make([]byte, HeaderSize)
	if _, err := io.ReadFull(conn, headerBuf); err != nil {
		return nil, ProtocolError{Message: "failed to read response header", Err: err}
	}

	payloadLen, err := strconv.Atoi(strings.TrimSpace(string(headerBuf)))
	if err != nil {
		return nil, ProtocolError{Message: "invalid response header length", Err: err}
	}

	if payloadLen == 0 {
		return nil, nil
	}

	payloadBuf := make([]byte, payloadLen)
	if _, err := io.ReadFull(conn, payloadBuf); err != nil {
		return nil, ProtocolError{Message: "failed to read response payload", Err: err}
	}
	return payloadBuf, nil
}

func ParseResponse(payload []byte) Response {
	if payload == nil {
		return Response{}
	}
	parts := strings.Split(strings.TrimSpace(string(payload)), ";")
	if len(parts) == 1 {
		return Response{Status: parts[0]}
	}
	return Response{Status: parts[0], Message: parts[1]}
}
