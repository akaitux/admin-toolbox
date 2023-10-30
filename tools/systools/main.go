package systools

import (
	"admin-toolbox/workdir"
	log "github.com/sirupsen/logrus"
	"os"
)

func ClearExit(code int, wrkdir *workdir.Workdir) {
	log.Debug("Cleanup workdir...")
	os.RemoveAll(wrkdir.Fullpath)
	log.Debugf("Exit with code %d", code)
	os.Exit(code)
}
