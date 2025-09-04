package common

import (
	"context"
	"errors"
	"net"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

type Client struct {
	config ClientConfig
	conn   net.Conn
}

func NewClient(config ClientConfig) *Client {
	return &Client{config: config}
}

func (c *Client) Connect() error {
	conn, err := net.DialTimeout("tcp", c.config.ServerAddress, ConnectionTimeout)
	if err != nil {
		return err
	}
	c.conn = conn
	return nil
}

func (c *Client) Close() {
	if c.conn != nil {
		c.conn.Close()
	}
}

func (c *Client) handleShutdown(ctx context.Context) {
	<-ctx.Done()
	log.Infof("action: shutdown_signal_received | result: success | client_id: %s", c.config.ID)
	c.Close()
}

func (c *Client) StartClientLoop() {
	defer c.Close()
	log.Infof("action: start_client | result: success | client_id: %v | server_address: %v", c.config.ID, c.config.ServerAddress)
	if err := c.Connect(); err != nil {
		log.Errorf("action: connect | result: fail | client_id: %v | server_address: %v | error: %v", c.config.ID, c.config.ServerAddress, err)
		return
	}
	log.Infof("action: connect | result: success | client_id: %v | server_address: %v", c.config.ID, c.config.ServerAddress)

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	go c.handleShutdown(ctx)

	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		if ctx.Err() != nil {
			break
		}

		bet, err := loadBetFromEnv()
		if err != nil {
			log.Errorf("action: load_bet | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return
		}

		payload := bet.Serialize(c.config.ID)

		response, err := Send(c.conn, payload)
		if err != nil {
			if errors.Is(err, net.ErrClosed) {
				log.Infof("action: client_stopped_during_send | result: success | client_id: %v", c.config.ID)
				break
			}

			var protocolErr ProtocolError
			if errors.As(err, &protocolErr) {
				log.Errorf("action: send_bet | result: fail | client_id: %v | error_type: protocol_error | details: %v", c.config.ID, protocolErr.Message)
			} else {
				log.Errorf("action: send_bet | result: fail | client_id: %v | error_type: general | error: %v", c.config.ID, err)
			}
			time.Sleep(c.config.LoopPeriod)
			continue
		}

		if response.Status == "ok" || response.Status == "success" {
			log.Infof("action: apuesta_enviada | result: success | dni: %s | numero: %d", bet.ClientID, bet.BetNumber)
		} else {
			log.Warningf("action: apuesta_enviada | result: fail | client_id: %v | server_error: %s", c.config.ID, response.Message)
		}

		log.Infof("action: receive_message | result: success | client_id: %v | msg: %s;%s", c.config.ID, response.Status, response.Message)
		time.Sleep(c.config.LoopPeriod)
	}

	if ctx.Err() != nil {
		log.Infof("action: stop_client | result: success | client_id: %v", c.config.ID)
	} else {
		log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
	}
}
