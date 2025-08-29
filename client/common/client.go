package common

import (
	"errors"
	"os"
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
}

func NewClient(config ClientConfig) *Client {
	return &Client{config: config}
}

func (c *Client) StartClientLoop() {
	log.Infof("Client %s starting loop...", c.config.ID)

	shutdownChan := make(chan os.Signal, 1)
	signal.Notify(shutdownChan, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(shutdownChan)

	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		select {
		case <-shutdownChan:
			log.Infof("Client %s stopped due to shutdown signal", c.config.ID)
			return
		default:
		}

		bet, err := LoadBetFromEnv()
		if err != nil {
			log.Errorf("action: load_bet | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return
		}

		response, err := SendBet(c.config.ServerAddress, bet, c.config.ID)
		if err != nil {
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

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
