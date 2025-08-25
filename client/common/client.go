package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

type Bet struct {
	Name        string
	Surname     string
	ClientID    string
	dateOfBirth string
	betNumber   int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	go c.gracefulShutdown()
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		c.createClientSocket()

		bet, err := LoadBetFromEnv()
		if err != nil {
			log.Errorf("action: load_bet | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		serializedBet := serializeBet(bet, c.config.ID)
		log.Infof("bet: %v", string(serializedBet))
		err = sendMessageInChunks(c.conn, serializedBet)
		if err != nil {
			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		msg, err := bufio.NewReader(c.conn).ReadString('\n')
		c.conn.Close()

		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
			c.config.ID,
			msg,
		)

		time.Sleep(c.config.LoopPeriod)

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) gracefulShutdown() {
	quitChan := make(chan os.Signal, 1)
	signal.Notify(quitChan, syscall.SIGINT, syscall.SIGTERM)

	sig := <-quitChan
	log.Infof("action: shutdown | result: in_progress | signal: %v", sig)
	if c.conn != nil {
		c.conn.Close()
	}
	log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
	os.Exit(0)
}

func serializeBet(bet Bet, agencyId string) []byte {
	serialized := fmt.Sprintf("%s;%s;%s;%s;%s;%d\n", agencyId, bet.Name, bet.Surname, bet.ClientID, bet.dateOfBirth, bet.betNumber)
	return []byte(serialized)
}

func LoadBetFromEnv() (Bet, error) {
	name := os.Getenv("NOMBRE")
	surname := os.Getenv("APELLIDO")
	clientID := os.Getenv("DOCUMENTO")
	dateOfBirth := os.Getenv("NACIMIENTO")
	betNumberStr := os.Getenv("NUMERO")

	betNumber, err := strconv.Atoi(betNumberStr)
	if err != nil {
		return Bet{}, fmt.Errorf("invalid NUMERO: %v", err)
	}

	return Bet{
		Name:        name,
		Surname:     surname,
		ClientID:    clientID,
		dateOfBirth: dateOfBirth,
		betNumber:   betNumber,
	}, nil
}

func sendMessageInChunks(conn net.Conn, message []byte) error {
	const chunkSize = 1024
	totalLength := len(message)
	sentBytes := 0

	for sentBytes < totalLength {
		end := sentBytes + chunkSize
		if end > totalLength {
			end = totalLength
		}

		n, err := conn.Write(message[sentBytes:end])
		if err != nil {
			return err
		}
		sentBytes += n
	}

	log.Infof("action: send_message | result: success | bytes_sent: %d", sentBytes)
	return nil
}
