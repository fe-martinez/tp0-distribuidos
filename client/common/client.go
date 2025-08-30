package common

import (
	"bufio"
	"context"
	"fmt"
	"net"
	"os"
	"os/signal"
	"syscall"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

type ClientConfig struct {
	ID            string
	ServerAddress string
	MaxBatchSize  int
	MaxBatchBets  int
	DataFilePath  string
}

type Client struct {
	config  ClientConfig
	file    *os.File
	scanner *bufio.Scanner
	conn    net.Conn
	reader  *bufio.Reader
}

func NewClient(config ClientConfig) (*Client, error) {
	file, err := os.Open(config.DataFilePath)
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
		return fmt.Errorf("could not connect to server: %w", err)
	}
	c.conn = conn
	c.reader = bufio.NewReader(conn)
	log.Infof("Client %s connected to %s", c.config.ID, c.config.ServerAddress)
	return nil
}

func (c *Client) Close() {
	if c.file != nil {
		c.file.Close()
	}
	if c.conn != nil {
		c.conn.Close()
	}
	log.Infof("Client %s connection closed.", c.config.ID)
}

func (c *Client) StartClientLoop() {
	if err := c.Connect(); err != nil {
		log.Errorf("Client %s failed to connect: %v", c.config.ID, err)
		return
	}
	defer c.Close()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	var overflowBet *Bet = nil

	for {
		if ctx.Err() != nil {
			log.Infof("Client %s stopped due to shutdown signal.", c.config.ID)
			return
		}

		batchResult, err := CreateBatch(c.scanner, c.config.MaxBatchSize, c.config.MaxBatchBets, overflowBet)
		if err != nil {
			log.Errorf("Failed to create batch: %v", err)
			return
		}

		overflowBet = batchResult.OverflowBet

		if len(batchResult.Batch.bets) > 0 {
			response, err := SendBatch(c.conn, c.reader, batchResult.Batch, c.config.ID)
			if err != nil {
				log.Errorf("Failed to send batch: %v", err)
				return
			}
			log.Debugf("action: send_batch | result: success | client_id: %s | server_status: %s | bets_sent: %d", c.config.ID, response.Status, len(batchResult.Batch.bets))
		}

		if len(batchResult.Batch.bets) == 0 && overflowBet == nil {
			log.Infof("End of file reached. Client finished processing.")
			break
		}
	}

	log.Infof("Client %s finished sending all bets.", c.config.ID)
}
