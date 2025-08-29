package common

import (
	"bufio"
	"fmt"
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

func SendBatch(conn net.Conn, batch Batch, agencyID string) (Response, error) {
	if err := conn.SetWriteDeadline(time.Now().Add(ConnectionTimeout)); err != nil {
		return Response{}, fmt.Errorf("failed to set write timeout: %w", err)
	}

	var builder strings.Builder
	builder.WriteString(fmt.Sprintf("%s;%d\n", agencyID, len(batch.bets)))

	for _, bet := range batch.bets {
		builder.WriteString(bet.SerializeBet())
	}

	if err := writeAll(conn, []byte(builder.String())); err != nil {
		return Response{}, ProtocolError{Message: "failed to send batch message", Err: err}
	}

	if err := conn.SetReadDeadline(time.Now().Add(ReadTimeout)); err != nil {
		return Response{}, fmt.Errorf("failed to set read timeout: %w", err)
	}

	responseStr, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return Response{}, ProtocolError{Message: "failed to receive response for batch", Err: err}
	}

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
