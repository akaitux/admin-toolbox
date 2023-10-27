package main

import (
	"github.com/akaitux/admin-toolbox/cmd"
)

var (
	Version   = "dev"
	BuildTime = "unknown"
)

func main() {
	cmd.Execute(Version, BuildTime)
}
