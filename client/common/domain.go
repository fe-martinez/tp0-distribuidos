package common

import (
	"bufio"
	"fmt"
	"strings"
)

type Bet struct {
	Name        string
	Surname     string
	ClientID    string
	DateOfBirth string
	BetNumber   string
}

func (b Bet) SerializeBet() string {
	return fmt.Sprintf(
		"%s;%s;%s;%s;%s\n",
		b.Name, b.Surname, b.ClientID, b.DateOfBirth, b.BetNumber,
	)
}

func (b Bet) GetBytesSize() int {
	return len(b.SerializeBet())
}

type Batch struct {
	Bets        []Bet
	CurrentSize int
	CurrentBets int
}

type BatchResult struct {
	Batch       Batch
	OverflowBet *Bet
}

func CreateBatch(scanner *bufio.Scanner, maxSize int, maxBets int, initialBet *Bet) (BatchResult, error) {
	batch := Batch{}
	var overflowBet *Bet

	if initialBet != nil {
		betSize := initialBet.GetBytesSize()
		if betSize <= maxSize && 1 <= maxBets {
			batch.Bets = append(batch.Bets, *initialBet)
			batch.CurrentSize += betSize
			batch.CurrentBets++
		} else {
			return BatchResult{Batch: batch, OverflowBet: initialBet}, nil
		}
	}

	for scanner.Scan() {
		fields := strings.Split(scanner.Text(), ",")
		if len(fields) != 5 {
			continue
		}

		bet := Bet{fields[0], fields[1], fields[2], fields[3], fields[4]}
		betSize := bet.GetBytesSize()

		if (batch.CurrentSize+betSize > maxSize && batch.CurrentSize > 0) ||
			(batch.CurrentBets+1 > maxBets && batch.CurrentBets > 0) {
			overflowBet = &bet
			break
		}

		batch.Bets = append(batch.Bets, bet)
		batch.CurrentSize += betSize
		batch.CurrentBets++
	}

	if err := scanner.Err(); err != nil {
		return BatchResult{}, fmt.Errorf("failed to scan input file: %w", err)
	}

	return BatchResult{Batch: batch, OverflowBet: overflowBet}, nil
}
