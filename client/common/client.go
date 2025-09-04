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
	filepath := fmt.Sprintf("/.data/agency-%s.csv", config.ID)
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
	if c.scanner != nil {
		c.scanner = nil
	}
	log.Infof("action: client_close | result: success | client_id: %s", c.config.ID)
}

func (c *Client) handleShutdown(ctx context.Context) {
	<-ctx.Done()
	log.Infof("action: shutdown_signal_received | result: success | client_id: %s", c.config.ID)
	c.Close()
}

func (c *Client) StartClientLoop() {
	defer c.Close()
	if err := c.Connect(); err != nil {
		log.Errorf("Client %s failed to connect: %v", c.config.ID, err)
		return
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	go c.handleShutdown(ctx)

	batch := NewBatch(c.config.MaxBatchSize, c.config.MaxBatchBets)

	for c.scanner.Scan() {
		if ctx.Err() != nil {
			log.Infof("action: stop_sending | result: success | client_id: %s", c.config.ID)
			return
		}

		line := c.scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) != 5 {
			log.Warningf("Skipping malformed line: %s", line)
			continue
		}
		bet := Bet{fields[0], fields[1], fields[2], fields[3], fields[4]}

		if !batch.Add(bet) {
			if err := c.sendBatch(batch); err != nil {
				log.Errorf("action: send_batch | result: fail | client_id: %s | error: %v", c.config.ID, err)
				return
			}

			batch = NewBatch(c.config.MaxBatchSize, c.config.MaxBatchBets)
			batch.Add(bet)
		}
	}

	if err := c.scanner.Err(); err != nil {
		log.Errorf("action: read_file | result: fail | client_id: %s | error: %v", c.config.ID, err)
		return
	}

	if batch.BetCount() > 0 {
		if err := c.sendBatch(batch); err != nil {
			log.Errorf("action: send_batch | result: fail | client_id: %s | error: %v", c.config.ID, err)
			return
		}
	}

	log.Infof("action: read_file | result: success | client_id: %s", c.config.ID)
}

func (c *Client) sendBatch(batch *Batch) error {
	payload := batch.Serialize(c.config.ID)
	if payload == nil {
		return nil
	}

	if err := Send(c.conn, payload); err != nil {
		log.Errorf("Failed to send batch: %v", err)
		return err
	}

	response, err := Receive(c.conn)
	if err != nil {
		log.Errorf("Failed to receive acknowledgment: %v", err)
		return err
	}

	if response.Status == "error" {
		log.Errorf("action: send_batch | result: fail | client_id: %s | message: %s", c.config.ID, response.Message)
		return fmt.Errorf("server error: %s", response.Message)
	}

	log.Infof("action: send_batch | result: success | client_id: %s | server_status: %s | bets_sent: %d", c.config.ID, response.Status, batch.BetCount())
	return nil
}
