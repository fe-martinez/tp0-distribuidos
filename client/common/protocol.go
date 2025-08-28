package common

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"strings"
)

type Response struct {
	Status  string
	Message string
}

func SendBet(serverAddress string, bet Bet, agencyID string) (Response, error) {
	conn, err := net.Dial("tcp", serverAddress)
	if err != nil {
		return Response{}, fmt.Errorf("could not connect to server: %w", err)
	}
	defer conn.Close()

	message := fmt.Sprintf("%s;%s;%s;%s;%s;%d\n", agencyID, bet.Name, bet.Surname, bet.ClientID, bet.DateOfBirth, bet.BetNumber)

	if _, err := io.WriteString(conn, message); err != nil {
		return Response{}, fmt.Errorf("failed to send message: %w", err)
	}

	response, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return Response{}, fmt.Errorf("failed to receive response: %w", err)
	}

	response = strings.TrimSpace(response)
	log.Infof("Received raw response: '%s'", response)

	parts := strings.Split(response, ",")
	if len(parts) < 2 {
		return Response{}, fmt.Errorf("invalid server response format: '%s'", response)
	}

	status := parts[0]
	value := parts[1]

	// Handle additional success statuses if needed
	if status != "ok" && status != "success" {
		return Response{}, fmt.Errorf("server returned failure status: '%s', message: '%s'", status, value)
	}

	return Response{Status: status, Message: value}, nil
}
