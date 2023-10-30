package main

import (
	"admin-toolbox/cmd"
)

var (
	Version   = "dev"
	BuildTime = "unknown"
    ConfDir   = "/opt/admin-toolbox"
)

func main() {
	cmd.Execute(Version, BuildTime, ConfDir)
}
