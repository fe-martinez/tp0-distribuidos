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

func SendBet(serverAddress string, bet Bet, agencyID string) (Response, error) {
	conn, err := net.DialTimeout("tcp", serverAddress, ConnectionTimeout)
	if err != nil {
		return Response{}, fmt.Errorf("could not connect to server: %w", err)
	}
	defer conn.Close()

	message := fmt.Sprintf(
		"%s;%s;%s;%s;%s;%d\n",
		agencyID,
		bet.Name,
		bet.Surname,
		bet.ClientID,
		bet.DateOfBirth,
		bet.BetNumber,
	)

	if err := writeAll(conn, []byte(message)); err != nil {
		return Response{}, ProtocolError{Message: "failed to send message", Err: err}
	}

	if err := conn.SetReadDeadline(time.Now().Add(ReadTimeout)); err != nil {
		return Response{}, fmt.Errorf("failed to set read timeout: %w", err)
	}

	responseStr, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return Response{}, ProtocolError{Message: "failed to receive response", Err: err}
	}

	parts := strings.Split(strings.TrimSpace(responseStr), ";")
	if len(parts) != 2 {
		return Response{}, ProtocolError{
			Message: fmt.Sprintf("invalid server response format: expected %d fields, got %d", 2, len(parts)),
		}
	}

	return Response{
		Status:  strings.TrimSpace(parts[0]),
		Message: strings.TrimSpace(parts[1]),
	}, nil
}
