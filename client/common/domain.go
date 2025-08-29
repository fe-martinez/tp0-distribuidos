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
	bets        []Bet
	currentSize int
	currentBets int
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
			batch.bets = append(batch.bets, *initialBet)
			batch.currentSize += betSize
			batch.currentBets++
		} else {
			overflowBet = initialBet
			return BatchResult{Batch: batch, OverflowBet: overflowBet}, nil
		}
	}

	for scanner.Scan() {
		line := scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) != 5 {
			continue
		}

		bet := Bet{fields[0], fields[1], fields[2], fields[3], fields[4]}
		betSize := bet.GetBytesSize()

		if (batch.currentSize+betSize > maxSize && batch.currentSize > 0) || (batch.currentBets+1 > maxBets && batch.currentBets > 0) {
			overflowBet = &bet
			break
		}

		batch.currentSize += betSize
		batch.currentBets++
		batch.bets = append(batch.bets, bet)
	}

	return BatchResult{Batch: batch, OverflowBet: overflowBet}, scanner.Err()
}
