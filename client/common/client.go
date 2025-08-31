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
		return fmt.Errorf("could not connect to server: %w", err)
	}
	c.conn = conn
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

	log.Infof("Client %s starting to send bets.", c.config.ID)
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
			response, err := SendBatch(c.conn, batchResult.Batch, c.config.ID)
			if err != nil {
				log.Errorf("Failed to send batch: %v", err)
				return
			}
			log.Debugf("action: send_batch | result: success | server_status: %s", response.Status)
		}

		if len(batchResult.Batch.bets) == 0 && overflowBet == nil {
			log.Infof("End of file reached. All bets sent.")
			break
		}
	}

	log.Infof("Finished sending all bets. Sending END signal.")
	if err := SendEndSignal(c.conn); err != nil {
		log.Errorf("Failed to send END signal: %v", err)
		return
	}

	log.Infof("Waiting for lottery results for agency %s...", c.config.ID)
	winners, err := ReceiveWinners(c.conn)
	if err != nil {
		log.Errorf("Failed to receive lottery results: %v", err)
		return
	}

	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", len(winners))
}
