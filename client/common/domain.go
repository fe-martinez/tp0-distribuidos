package common

import (
	"fmt"
	"os"
	"strconv"
)

type Bet struct {
	Name        string
	Surname     string
	ClientID    string
	DateOfBirth string
	BetNumber   int
}

func LoadBetFromEnv() (Bet, error) {
	name := os.Getenv("NOMBRE")
	surname := os.Getenv("APELLIDO")
	clientID := os.Getenv("DOCUMENTO")
	dateOfBirth := os.Getenv("NACIMIENTO")
	betNumberStr := os.Getenv("NUMERO")

	if name == "" || surname == "" || clientID == "" || dateOfBirth == "" || betNumberStr == "" {
		return Bet{}, fmt.Errorf("one or more required environment variables are not set (NOMBRE, APELLIDO, DOCUMENTO, NACIMIENTO, NUMERO)")
	}

	betNumber, err := strconv.Atoi(betNumberStr)
	if err != nil {
		return Bet{}, fmt.Errorf("invalid NUMERO environment variable: %w", err)
	}

	return Bet{
		Name:        name,
		Surname:     surname,
		ClientID:    clientID,
		DateOfBirth: dateOfBirth,
		BetNumber:   betNumber,
	}, nil
}
