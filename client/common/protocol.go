package common

import (
	"bufio"
	"fmt"
	"net"
	"strings"
)

type Response struct {
	Status  string
	Message string
}

func writeAll(conn net.Conn, msg []byte) error {
	totalSent := 0
	for totalSent < len(msg) {
		sent, err := conn.Write(msg[totalSent:])
		if err != nil {
			return err
		}
		totalSent += sent
	}
	return nil
}

func SendBet(serverAddress string, bet Bet, agencyID string) (Response, error) {
	conn, err := net.Dial("tcp", serverAddress)
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
		return Response{}, fmt.Errorf("failed to send message: %w", err)
	}

	responseStr, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return Response{}, fmt.Errorf("failed to receive response: %w", err)
	}

	parts := strings.Split(strings.TrimSpace(responseStr), ";")
	if len(parts) < 2 {
		return Response{}, fmt.Errorf("invalid server response format: '%s'", responseStr)
	}

	return Response{Status: parts[0], Message: parts[1]}, nil
}
