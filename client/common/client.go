package common

import (
	"bufio"
	"context"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

type ClientConfig struct {
	ID            string
	ServerAddress string
	MaxBatchSize  int
	MaxBatchBets  int
}

type Client struct {
	config  ClientConfig
	file    *os.File
	scanner *bufio.Scanner
	conn    net.Conn
}

func NewClient(config ClientConfig) (*Client, error) {
	filepath := fmt.Sprintf("/.data/agency-%v.csv", config.ID)
	file, err := os.Open(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to open data file: %w", err)
	}
	return &Client{
		config:  config,
		file:    file,
		scanner: bufio.NewScanner(file),
	}, nil
}

func (c *Client) Connect() error {
	conn, err := net.DialTimeout("tcp", c.config.ServerAddress, ConnectionTimeout)
	if err != nil {
		return fmt.Errorf("actions: connect | result: fail | client_id: %s | server_address: %s | error: %v", c.config.ID, c.config.ServerAddress, err)
	}
	c.conn = conn
	log.Infof("action: connect | result: success | client_id: %s | server_address: %s", c.config.ID, c.config.ServerAddress)
	return nil
}

func (c *Client) Close() {
	if c.file != nil {
		c.file.Close()
	}
	if c.conn != nil {
		c.conn.Close()
	}
	log.Infof("action: close_connection | result: success | client_id: %s", c.config.ID)
}

func (c *Client) StartClientLoop() {
	if err := c.Connect(); err != nil {
		log.Errorf("actions: start_client_loop | result: fail | client_id: %s | error: %v", c.config.ID, err)
		return
	}
	defer c.Close()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	log.Infof("action: start_sending | result: success | client_id: %s", c.config.ID)
	batch := NewBatch(c.config.MaxBatchSize, c.config.MaxBatchBets)

	for c.scanner.Scan() {
		if ctx.Err() != nil {
			log.Infof("action: stop_sending | result: success | client_id: %s", c.config.ID)
			return
		}

		line := c.scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) != 5 {
			continue
		}
		bet := Bet{fields[0], fields[1], fields[2], fields[3], fields[4]}

		if !batch.Add(bet) {
			c.sendBatch(batch)

			batch = NewBatch(c.config.MaxBatchSize, c.config.MaxBatchBets)
			batch.Add(bet)
		}
	}

	if !batch.IsEmpty() {
		c.sendBatch(batch)
	}
	log.Infof("action: end_of_file | result: success | client_id: %s", c.config.ID)

	c.sendEndSignal()
	c.receiveAndLogWinners()
}

func (c *Client) sendBatch(batch *Batch) {
	payload := batch.Serialize(c.config.ID)
	if err := Send(c.conn, payload); err != nil {
		log.Errorf("action: send_batch | result: fail | client_id: %s | error: %v", c.config.ID, err)
		return
	}

	responsePayload, err := Receive(c.conn, ReadTimeout)
	if err != nil {
		log.Errorf("action: receive_ack | result: fail | client_id: %s | error: %v", c.config.ID, err)
		return
	}
	response := ParseResponse(responsePayload)
	log.Debugf("action: send_batch | result: success | server_status: %s | bets_sent: %d", response.Status, batch.BetCount())
}

func (c *Client) sendEndSignal() {
	endMessage := []byte(fmt.Sprintf("%-*s", HeaderSize, "END"))

	if err := writeAll(c.conn, endMessage); err != nil {
		log.Errorf("action: send_end_signal | result: fail | client_id: %s | error: %v", c.config.ID, err)
		return
	}
	log.Infof("action: send_end_signal | result: success | client_id: %s", c.config.ID)
}

func (c *Client) receiveAndLogWinners() {
	longReadTimeout := 30 * time.Second
	winnersPayload, err := Receive(c.conn, longReadTimeout)
	if err != nil {
		log.Errorf("action: consulta_ganadores | result: fail | client_id: %s | error: %v", c.config.ID, err)
		return
	}

	var winners []string
	if len(winnersPayload) > 0 {
		winners = strings.Split(string(winnersPayload), ";")
	}

	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", len(winners))
}
