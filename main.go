package main

import (
	"github.com/akaitux/admin-toolbox/cmd"
)

var (
	Version   = "dev"
	BuildTime = "unknown"
    ConfDir   = "/opt/admin-toolbox"
)

func main() {
	cmd.Execute(Version, BuildTime, ConfDir)
}
