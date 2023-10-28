package cmd

import (
    "os"
    log "github.com/sirupsen/logrus"
)


func exit(code int) {
    log.Debug("Cleanup workdir...")
    os.RemoveAll(Config.Workdir)
    log.Debugf("Exit with code %d", code)
    os.Exit(code)
}
