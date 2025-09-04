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

func SendBatch(conn net.Conn, batch Batch, agencyID string) (Response, error) {
	payload := fmt.Sprintf("%s;%d\n", agencyID, len(batch.Bets))
	for _, bet := range batch.Bets {
		payload += bet.SerializeBet()
	}

	header := fmt.Sprintf("%0*d", HeaderSize, len(payload))
	fullMessage := []byte(header + payload)

	if err := conn.SetWriteDeadline(time.Now().Add(WriteTimeout)); err != nil {
		return Response{}, fmt.Errorf("failed to set write deadline: %w", err)
	}
	defer conn.SetWriteDeadline(time.Time{})

	if _, err := conn.Write(fullMessage); err != nil {
		return Response{}, ProtocolError{Message: "failed to write batch message", Err: err}
	}

	return readStandardResponse(conn)
}

func SendEndSignal(conn net.Conn) error {
	endMessage := fmt.Sprintf("%-*s", HeaderSize, "END")

	if err := conn.SetWriteDeadline(time.Now().Add(WriteTimeout)); err != nil {
		return fmt.Errorf("failed to set write deadline: %w", err)
	}
	defer conn.SetWriteDeadline(time.Time{})

	if _, err := conn.Write([]byte(endMessage)); err != nil {
		return ProtocolError{Message: "failed to write END message", Err: err}
	}
	return nil
}

func ReceiveWinners(conn net.Conn) ([]string, error) {
	const longReadTimeout = 30 * time.Second

	response, err := readWinnerResponse(conn, longReadTimeout)
	if err != nil {
		return nil, err
	}

	if response == "NO_WINNERS" || strings.TrimSpace(response) == "" {
		return []string{}, nil
	}

	winners := strings.Split(response, ";")
	return winners, nil
}

func readStandardResponse(conn net.Conn) (Response, error) {
	if err := conn.SetReadDeadline(time.Now().Add(ReadTimeout)); err != nil {
		return Response{}, fmt.Errorf("failed to set read deadline: %w", err)
	}
	defer conn.SetReadDeadline(time.Time{})

	respHeaderBuf := make([]byte, HeaderSize)
	if _, err := io.ReadFull(conn, respHeaderBuf); err != nil {
		return Response{}, ProtocolError{Message: "failed to read response header", Err: err}
	}

	respLen, err := strconv.Atoi(strings.TrimSpace(string(respHeaderBuf)))
	if err != nil {
		return Response{}, ProtocolError{Message: "invalid response header length", Err: err}
	}

	if respLen == 0 {
		return Response{}, nil
	}

	respPayloadBuf := make([]byte, respLen)
	if _, err := io.ReadFull(conn, respPayloadBuf); err != nil {
		return Response{}, ProtocolError{Message: "failed to read response payload", Err: err}
	}

	parts := strings.Split(strings.TrimSpace(string(respPayloadBuf)), ";")
	if len(parts) == 0 {
		return Response{}, ProtocolError{Message: "empty response payload"}
	}

	if len(parts) == 1 {
		return Response{Status: strings.TrimSpace(parts[0])}, nil
	}

	return Response{
		Status:  strings.TrimSpace(parts[0]),
		Message: strings.TrimSpace(parts[1]),
	}, nil
}

func readWinnerResponse(conn net.Conn, timeout time.Duration) (string, error) {
	if err := conn.SetReadDeadline(time.Now().Add(timeout)); err != nil {
		return "", fmt.Errorf("failed to set read deadline: %w", err)
	}
	defer conn.SetReadDeadline(time.Time{})

	respHeaderBuf := make([]byte, HeaderSize)
	if _, err := io.ReadFull(conn, respHeaderBuf); err != nil {
		return "", ProtocolError{Message: "failed to read winners header", Err: err}
	}

	respLen, err := strconv.Atoi(strings.TrimSpace(string(respHeaderBuf)))
	if err != nil {
		return "", ProtocolError{Message: "invalid winners header length", Err: err}
	}

	if respLen == 0 {
		return "", nil
	}

	respPayloadBuf := make([]byte, respLen)
	if _, err := io.ReadFull(conn, respPayloadBuf); err != nil {
		return "", ProtocolError{Message: "failed to read winners payload", Err: err}
	}

	return strings.TrimSpace(string(respPayloadBuf)), nil
}
