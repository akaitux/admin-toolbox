package cmd

import (
    log "github.com/sirupsen/logrus"
)

func Run() {
    log.Errorf("%v", Config)
}
