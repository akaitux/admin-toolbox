package cmd

import (
    "os"
    "admin-toolbox/config"
    log "github.com/sirupsen/logrus"
)


func exit(code int) {
    log.Debug("Cleanup workdir...")
    os.RemoveAll(config.Config.Workdir)
    log.Debugf("Exit with code %d", code)
    os.Exit(code)
}
