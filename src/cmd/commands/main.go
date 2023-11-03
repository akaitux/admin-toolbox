package commands

import (
	"admin-toolbox/cmd/atCli"
	"admin-toolbox/cmd/run"
	"github.com/spf13/cobra"
)

func AddCommands(cmd *cobra.Command, cli *atCli.Cli) {
	cmd.AddCommand(
		run.NewRunCommand(cli),
	)
}
