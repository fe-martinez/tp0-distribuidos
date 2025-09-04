package common

import (
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
	maxSize     int
	maxBets     int
}

func NewBatch(maxSize int, maxBets int) *Batch {
	return &Batch{
		maxSize: maxSize,
		maxBets: maxBets,
		bets:    make([]Bet, 0),
	}
}

func (b *Batch) Add(bet Bet) bool {
	betSize := bet.GetBytesSize()
	if (b.currentSize+betSize > b.maxSize && !b.IsEmpty()) || (b.currentBets+1 > b.maxBets && !b.IsEmpty()) {
		return false
	}
	b.bets = append(b.bets, bet)
	b.currentSize += betSize
	b.currentBets++
	return true
}

func (b *Batch) Serialize(agencyID string) []byte {
	var builder strings.Builder
	builder.WriteString(fmt.Sprintf("%s;%d\n", agencyID, len(b.bets)))
	for _, bet := range b.bets {
		builder.WriteString(bet.SerializeBet())
	}
	return []byte(builder.String())
}

func (b *Batch) IsEmpty() bool {
	return len(b.bets) == 0
}

func (b *Batch) BetCount() int {
	return len(b.bets)
}
